import time
import pyupbit
import datetime
import numpy as np
import pandas as pd

# UPbit API 키
access = ""
secret = ""


# UPbit 객체 생성
upbit = pyupbit.Upbit(access, secret)

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance():
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == 'KRW':
            if b['balance'] is not None:
                return int(float(b['balance']))  # float 형태를 먼저 변환 후 int로 형변환
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def calculate_rsi(data, window=14):
    """RSI 계산"""
    if len(data) >= window:  # 데이터가 유효한지 확인
        diff = data.diff(1)
        gain = (diff.where(diff > 0, 0)).rolling(window=window).mean()
        loss = (-diff.where(diff < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]  # 최신 RSI 값 반환
    else:
        return None

# 매수한 코인의 가격 저장하는 변수
bought_prices = {}

# 손절한 코인의 최종 시간 저장하는 변수
banned_coins = {}

# 최소 구매 가능 금액
min_bid_amount = 5000

# 자동매매 시작
print("autotrade start")
while True:
    try:
        now = datetime.datetime.now()
        total_balance = get_balance()  # 현재 보유 현금 조회

        # 코인 목록
        coins = ["KRW-BTC", "KRW-XRP", "KRW-ETC", "KRW-SC", "KRW-ETH", 
                 "KRW-DOGE", "KRW-CHZ", "KRW-LOOM", "KRW-MTL", "KRW-GLM",
                 "KRW-HUNT", "KRW-STX", "KRW-PLA", "KRW-SOL", "KRW-MATIC",
                 "KRW-SAND", "KRW-HIVE", "KRW-FLOW", "KRW-IOTA", "KRW-BORA"]
        
        for coin in coins:
            if coin in bought_prices:
                continue  # 이미 매수한 코인은 건너뜁니다.
            
            df = pyupbit.get_ohlcv(coin, interval="minute60", count=14)
            current_price = get_current_price(coin)
            rsi = calculate_rsi(df['close'])
            
            # RSI가 35 미만이면서 보유 현금이 최소 구매 가능 금액 이상일 때 매수 진행
            if rsi is not None and rsi < 35 and total_balance >= min_bid_amount:
                # 현재 보유 현금의 30%를 해당 코인에 투자
                buying_amount = int(total_balance * 0.3)  # float 형태를 먼저 변환 후 int로 형변환
                if buying_amount >= min_bid_amount:  # 최소 구매 가능 금액 이상인지 확인
                    # 매수 주문 실행
                    upbit.buy_market_order(coin, buying_amount)
                    bought_prices[coin] = (current_price, buying_amount)
                    print(f"{coin} 매수 완료 - 매수 금액: {buying_amount}")

        # 손절 체크
        for coin, (buying_price, buying_amount) in list(bought_prices.items()):  # 리스트로 변환하여 변경 중 오류 방지
            current_price = get_current_price(coin)
            if current_price is not None:
                if current_price <= buying_price * 0.96:  # 현재가가 매수가격의 4% 이하 하락 시 손절
                    upbit.sell_market_order(coin, buying_amount)  # 보유량 전량 매도
                    print(f"{coin} 손절 완료 - 손절 가격: {current_price}")
                    banned_coins[coin] = now  # 해당 코인을 banned_coins에 추가하여 재매수 방지
                    del bought_prices[coin]  # 손절한 코인 삭제

        # 24시간 동안 거래하지 않은 코인을 banned_coins에서 삭제
        for coin, banned_time in banned_coins.copy().items():
            if now - banned_time >= datetime.timedelta(days=1):
                del banned_coins[coin]
            
            # 매수한 코인 역시 24시간 이후에 재구매 가능하도록 변경
            if coin in bought_prices and now - banned_time >= datetime.timedelta(days=1):
                del bought_prices[coin]
                 
        time.sleep(60)  # 60초마다 반복
        
    except Exception as e:
        print(e)
        time.sleep(60)
