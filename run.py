import pybithumb
import datetime
import numpy as np
import time

My = pybithumb.Bithumb("conkey", "seckey")

def get_target_price(ticker, k):
    df = pybithumb.get_ohlcv(ticker)[-2:]
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_ma5(ticker):
    df = pybithumb.get_ohlcv(ticker)[-6:]
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5


def get_current_price(ticker):
    return pybithumb.get_current_price(ticker)

def get_ror(k=0.5):
    df = pybithumb.get_ohlcv("ONDO")[-8:]
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    fee = 0.0032
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'] - fee,
                         1)

    ror = df['ror'].cumprod().iloc[-2]
    return ror

def find_best_k():
    best_k, best_ror = -1, 0
    for k in np.arange(0.05, 1.01, 0.05):
        ror = get_ror(k)
        if ror > best_ror:
            best_ror = ror
            best_k = k
    return best_k

#시장가로 코인 매수
def buy_crypto_currency(krw, ticker):
    #호가창 조회
    orderbook = pybithumb.get_orderbook(ticker)
    sell_price = orderbook['asks'][0]['price']
    unit = krw / float(sell_price)
    My.buy_market_order(ticker, unit)

#시장가로 코인 매도
def sell_crypto_currency(ticker):
    unit = My.get_balance(ticker)[0]
    My.sell_market_order(ticker, unit)



high_price = 0
buy_price = 0

while True:
    bk = find_best_k()
    try:
        target_price = get_target_price("ONDO", bk)
        ma5 = get_ma5("ONDO")
        current_price = get_current_price("ONDO")
        krw = My.get_balance("ONDO")[2]
        #매수가 되었다면 최고가 갱신
        if buy_price > 0:
            high_price = max(high_price, current_price)
        print("target price : ", target_price, "ma5 : ", ma5, "current_price : ", current_price, "high price : ", high_price)
        if target_price < current_price and ma5 < current_price:
            buy_order_amount = krw*0.8
            if buy_order_amount > 5000:
                print("매수합니다.")
                buy_price = current_price
                buy_crypto_currency(buy_order_amount, "ONDO")

        unit = My.get_balance("ONDO")[0]
        if buy_price > 0 and unit > 0:
            last_buy_price = buy_price
            hand_cut_price = last_buy_price * 0.95  # 5% 이하로 빠졌을 때 매도 가격
            profit_price = high_price * 0.95  # 최고가 기준 5 이하 하락 했을 때 매도 가격
            if current_price == high_price:
                continue
                
            if current_price < hand_cut_price:
                print("손절합니다.")
                sell_crypto_currency("ONDO")

            if last_buy_price < current_price < profit_price:
                print("익절합니다.")
                sell_crypto_currency("ONDO")

        time.sleep(1)

    except Exception as e:
        print("error : ", e)
        time.sleep(1)
