import pybithumb
import numpy as np
import time

#여기에 connect key와 secret key를 입력한다. ex) "abcdef", "ghijklmn"
My = pybithumb.Bithumb("conkey", "seckey")

#여기에 ticker를 입력한다. ex) 비트코인이면 "BTC", 온도 코인이면 "ONDO" 
my_ticker = "Write coin ticker here"

#목표값 계산
def get_target_price(ticker, k):
    df = pybithumb.get_ohlcv(ticker)[-1:]
    target_price = df.iloc[0]['low'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

# 5일간의 이동평균선 계산
def get_ma5(ticker):
    df = pybithumb.get_ohlcv(ticker)[-6:]
    mA5 = df['low'].rolling(5).mean().iloc[-1]
    return mA5

#해당 코인의 현재 가격
def get_current_price(ticker):
    return pybithumb.get_current_price(ticker)

#수익률 계산
def get_ror(ticker, k):
    df = pybithumb.get_ohlcv(ticker)[-8:]
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    fee = 0.04
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'] - fee,
                         1)

    ror = df['ror'].cumprod().iloc[-2]
    return ror

#최적의 k값 계산
def find_best_k(ticker):
    best_k, best_ror = -1, 0
    for k in np.arange(0.05, 1.01, 0.05):
        ror = get_ror(ticker, k)
        if ror > best_ror:
            best_ror = ror
            best_k = k
    return best_k


# 시장가로 코인 매수
def buy_crypto_currency(krw, ticker):
    # 호가창 조회
    orderbook = pybithumb.get_orderbook(ticker)
    sell_price = orderbook['asks'][0]['price']
    unit = krw / float(sell_price)
    print("매수 unit : ", unit)
    My.buy_market_order(ticker, unit)


# 시장가로 코인 매도
def sell_crypto_currency(ticker):
    unit = My.get_balance(ticker)[0]
    My.sell_market_order(ticker, unit)


#buy_price : 매수값, sell_price : 매도값, low_price : 매수 전 최저가 cal_k : bk 값 갱신 주기, bk : 수익률 계산 함수에서 계산한 최적의 k 값
buy_price = 0
sell_price = 100000
low_price = 100000
cal_k = 70000
bk = find_best_k(my_ticker)
flag = True

while True:
    try:
        if cal_k == 0:
            bk = find_best_k(my_ticker)
            cal_k = 70000
        #print("bk : ", bk)
        cal_k -= 1
        #Target_price : 목표값, ma5 : 5일 평균선, current_price : 해당 코인의 현재가, Krw : 현재 내가 보유한 원화량, MY_unit : 내가 보유한 코인량
        Target_price = get_target_price(my_ticker, bk)
        ma5 = get_ma5(my_ticker)
        current_price = get_current_price(my_ticker)
        Krw = My.get_balance(my_ticker)[2]
        MY_unit = My.get_balance(my_ticker)[0]
        TH_price = sell_price * 0.97
        #print("buy price : ", buy_price, "Krw : ", Krw)
        #print("보유 코인수 : ", MY_unit)
        # 매수가 되었다면 최고가 갱신
        if buy_price == 0:
            low_price = min(low_price, current_price)
        # TH_price : 다시 매수할 때에는 최근에 매도한 가격의 97% 가격을 임계값으로 설정
        # 만약 TH_price가 Target_price나 ma5의 최대값보다 작으면 매수가 안되므로 그 값의 1.02값으로 변경
        if flag == False and current_price >= low_price * 1.03:
            flag = True
        #print("target price : ", Target_price, "ma5 : ", ma5)
        #print("current_price : ", current_price, "high price : ", high_price)

        # 만약 내가 매수를 하지 않았으면 매수 진행
        if buy_price == 0:
            # 현재가가 Target_price와 ma5 이상이면 상승장에 진입했다고 판단함. 그리고 TH_price보다 작으면 매수 진행
            if Target_price < current_price and ma5 < current_price and flag == True:
                #현재 내가 보유한 원화량의 70%를 매수. 이유는 모르겠으나 이 가격이상으로는 오류가 발생해서 매수가 안됨
                #혹시 매수할 금액을 변경하고 싶으면 buy_order_amount를 바꿔주면 된다.
                #ex. 10만원어치를 매수하고 싶으면 buy_order_amount = 100000  
                buy_order_amount = round(Krw * 0.7)
                #print("매수량 : ", buy_order_amount)
                #print("매수합니다.")
                #print("매수 금액 : ", current_price)
                buy_crypto_currency(buy_order_amount, my_ticker)
                buy_price = current_price
                low_price = 100000
        
        #내가 매수를 진행했으면 매도 진행
        elif buy_price > 0 and MY_unit > 0:
            #last_buy_price : 현재 매수가, hand_cut_price : 손절가, 매수가에서 3%이상 떨어지면 손절, profit_price : 익절가, 최고가 기준 3%이상 떨어지면 익절
            last_buy_price = buy_price
            hand_cut_price = last_buy_price * 0.97
            profit_price = last_buy_price * 1.05
            
            #손절가 이하로 떨어지면 매도도
            if current_price < hand_cut_price:
                #print("손절합니다.")
                #print("손절가 : ", current_price)
                sell_crypto_currency(my_ticker)
                sell_price = current_price
                buy_price = 0
                flag = False

            #익절가 이하로 떨어지면 익절
            elif last_buy_price < current_price < profit_price:
                #print("익절합니다.")
                #print("익절가 : ", current_price)
                sell_crypto_currency(my_ticker)
                sell_price = current_price
                buy_price = 0

        time.sleep(1)

    except Exception as e:
        print("error : ", e)
        time.sleep(1)
