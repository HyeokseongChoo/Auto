import time
import pyupbit
import datetime
import numpy as np
import pandas as pd

# UPbit API 키
access = "Clfxtv6Xx8KmdPSTrRLcI3LTFtCAEXtCxU4d7OyU"
secret = "SUELYxkqxK5upfRtL2ns089xJ4F32hlQkllgR73V"

# 매수 가격을 저장할 딕셔너리
bought_prices = {}

# 코인 최소 구매 수량
MIN_ORDER_QUANTITY = 5000

def calculate_rsi(data, window=14):
    """RSI 계산"""
    diff = data.diff(1)
    gain = (diff.where(diff > 0, 0)).rolling(window=window).mean()
    loss = (-diff.where(diff < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(data, window=14):
    """ATR 계산"""
    high_low = data['high'] - data['low']
    high_prev_close = np.abs(data['high'] - data['close'].shift())
    low_prev_close = np.abs(data['low'] - data['close'].shift())
    ranges = pd.concat([high_low, high_prev_close, low_prev_close], axis=1)
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
                if df is None or df.empty:
                    print(f"Warning: {coin} 데이터가 없어 예측을 수행할 수 없습니다.")
                    continue
                current_price = pyupbit.get_current_price(coin)
                rsi = calculate_rsi(df['close'])
                atr = calculate_atr(df)
                if rsi.iloc[-1] < 35:  # RSI가 35 미만인 경우 매수
                    krw = upbit.get_balance("KRW")
                    if krw > MIN_ORDER_QUANTITY:  # 최소 주문 금액 이상인지 확인
                        buy_amount = min(krw * 0.5, krw - MIN_ORDER_QUANTITY)  # 잔고의 50%만 사용하여 매수
                        adjusted_price = buy_amount / current_price  # 적정 매수 수량 계산
                        if adjusted_price >= MIN_ORDER_QUANTITY:
                            upbit.buy_market_order(coin, adjusted_price)
                            bought_prices[coin] = current_price  # 매수 시점의 현재가를 기록합니다.
        else:
            for coin in ["KRW-BTC", "KRW-XRP", "KRW-ETC", "KRW-SC", "KRW-ETH", "KRW-DOGE", "KRW-CHZ", "KRW-LOOM", "KRW-MTL", "KRW-GLM","KRW-HUNT","KRW-STX","KRW-PLA","KRW-SOL", "KRW-MATIC","KRW-SAND", "KRW-HIVE", "KRW-FLOW", "KRW-IOTA","KRW-BORA"]:
                coin_balance = upbit.get_balance(coin.replace("KRW-", ""))
                if coin_balance * current_price > MIN_ORDER_QUANTITY:
                    current_price = pyupbit.get_current_price(coin)
                    if coin in bought_prices:
                        profit_ratio = (current_price / bought_prices[coin]) - 1
                        if profit_ratio >= 0.02:  # 구매 가격 대비 2% 이상 수익이면 전량 매도
                            upbit.sell_market_order(coin, coin_balance)
                            continue
                    if rsi.iloc[-1] > 70:  # RSI가 70을 넘어가면 전량 매도
                        upbit.sell_market_order(coin, coin_balance)
                        continue
                    if atr.iloc[-1] < current_price * 0.03:  # ATR이 현재 가격의 3%보다 작으면 전량 매도
                        upbit.sell_market_order(coin, coin_balance)
        
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
