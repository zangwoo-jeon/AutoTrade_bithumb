import pybithumb
import numpy as np
import time

My = pybithumb.Bithumb("conkey", "seckey")

my_ticker = "Write coin ticker here"

#목표값 계산
def get_target_price(ticker, k):
    df = pybithumb.get_ohlcv(ticker)[-2:]
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
    df['target'] = df['low'] + df['range'].shift(1)

    fee = 0.0032
    df['ror'] = np.where(df['high'] > df['target'],
                         (df['high']*0.95) / df['target'] - fee,
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


high_price = 0
buy_price = 0
sell_price = 100000
cal_k = 70000
bk = find_best_k(my_ticker)

while True:
    try:
        if cal_k == 0:
            bk = find_best_k(my_ticker)
            cal_k = 70000
        #print("bk : ", bk)
        cal_k -= 1
        Target_price = get_target_price(my_ticker, bk)
        ma5 = get_ma5(my_ticker)
        current_price = get_current_price(my_ticker)
        Krw = My.get_balance(my_ticker)[2]
        MY_unit = My.get_balance(my_ticker)[0]
        #print("buy price : ", buy_price, "Krw : ", Krw)
        #print("보유 코인수 : ", MY_unit)
        # 매수가 되었다면 최고가 갱신
        if buy_price > 0:
            high_price = max(high_price, current_price)
        TH_price = sell_price*0.97
        if TH_price < max(Target_price, ma5):
            TH_price = max(Target_price, ma5)*1.02
        #print("target price : ", Target_price, "ma5 : ", ma5)
        #print("current_price : ", current_price, "high price : ", high_price)

        if buy_price == 0:
            if Target_price < current_price and ma5 < current_price and current_price < TH_price:
                buy_order_amount = round(Krw * 0.7)
                #print("매수량 : ", buy_order_amount)
                #print("매수합니다.")
                #print("매수 금액 : ", current_price)
                buy_crypto_currency(buy_order_amount, my_ticker)
                buy_price = current_price

        elif buy_price > 0 and MY_unit > 0:
            last_buy_price = buy_price
            #hand_cut_price = last_buy_price * 0.95  # 5% 이하로 빠졌을 때 매도 가격
            hand_cut_price = last_buy_price * 0.95
            profit_price = high_price * 0.95  # 최고가 기준 5 이하 하락 했을 때 매도 가격
            if current_price == high_price:
                continue

            elif current_price < hand_cut_price:
                #print("손절합니다.")
                #print("손절가 : ", current_price)
                sell_crypto_currency(my_ticker)
                sell_price = current_price
                buy_price = 0
                high_price = 0

            elif last_buy_price < current_price < profit_price:
                #print("익절합니다.")
                #print("익절가 : ", current_price)
                sell_crypto_currency(my_ticker)
                sell_price = current_price
                buy_price = 0
                high_price = 0

        time.sleep(1)

    except Exception as e:
        print("error : ", e)
        time.sleep(1)
