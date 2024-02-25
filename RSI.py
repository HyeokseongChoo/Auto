import time
import pyupbit
import datetime
import numpy as np
import pandas as pd

# UPbit API 키
access = ""
secret = ""

# 코인 최소 구매 수량
MIN_ORDER_QUANTITY = 5000

# 구매한 코인의 가격 저장하는 변수
bought_prices = {}

# 구매한 코인의 최종 매수 시간 저장하는 변수
bought_times = {}

# 손절한 코인의 최종 시간 저장하는 변수
banned_coins = {}

def calculate_rsi(data, window=14):
    """RSI 계산"""
    diff = data.diff(1)
    gain = (diff.where(diff > 0, 0)).rolling(window=window).mean()
    loss = (-diff.where(diff < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(df, window=14):
    """ATR 계산"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(window=window).mean()
    return atr

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            for coin in ["KRW-BTC", "KRW-XRP", "KRW-ETC", "KRW-SC", "KRW-ETH", "KRW-DOGE", "KRW-CHZ", "KRW-LOOM", "KRW-MTL", "KRW-GLM","KRW-HUNT","KRW-STX","KRW-PLA","KRW-SOL", "KRW-MATIC","KRW-SAND", "KRW-HIVE", "KRW-FLOW", "KRW-IOTA","KRW-BORA"]:
                df = pyupbit.get_ohlcv(coin, interval="minute60", count=14)
                current_price = pyupbit.get_current_price(coin)
                rsi = calculate_rsi(df['close'])
                atr = calculate_atr(df)
                if rsi is not None and rsi.iloc[-1] < 35:  # RSI가 35 미만인 경우 매수
                    krw = upbit.get_balance("KRW")
                    if krw * 0.5 > MIN_ORDER_QUANTITY:  # 잔고의 50%가 최소 주문 금액 이상이면 매수
                        # 동일한 코인인지, 그리고 최종 매수 시간이 3시간 이상 경과했는지, 손절된 코인인지 확인
                        if coin not in bought_times or (now - bought_times[coin]).total_seconds() >= 10800:
                            if coin not in banned_coins or (now - banned_coins[coin]).total_seconds() >= 10800:
                                buy_amount = min(krw * 0.5, krw - MIN_ORDER_QUANTITY)  # 잔고의 50%만 사용하여 매수
                                adjusted_price = buy_amount  # 적정 매수 수량 계산
                                if adjusted_price >= MIN_ORDER_QUANTITY:
                                    upbit.buy_market_order(coin, adjusted_price)
                                    # 매수한 코인의 가격 및 시간 저장
                                    bought_prices[coin] = current_price
                                    bought_times[coin] = now
        else:
            for coin in bought_prices.keys():
                df = pyupbit.get_ohlcv(coin, interval="minute60", count=14)  
                current_price = pyupbit.get_current_price(coin)  
                rsi = calculate_rsi(df['close'])
                atr = calculate_atr(df)
                coin_balance = upbit.get_balance(coin.replace("KRW-", ""))
                if coin_balance * current_price > MIN_ORDER_QUANTITY:
                    if rsi.iloc[-1] > 70 or atr.iloc[-1] < current_price * 0.03:  
                        upbit.sell_market_order(coin, coin_balance)
                    elif bought_prices[coin] * 1.02 < current_price:  # 구매한 가격 대비 2% 이상 상승하면 전량 매도
                        upbit.sell_market_order(coin, coin_balance)
        
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
