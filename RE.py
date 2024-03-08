import pyupbit
import datetime
import time

# UPbit API 키
access = "9l8mPiSHbQzPpBmYYi8VLp6DQugEisRQcDathEy"
secret = "J5MspX1xDLqk5W6snxjHP8liCITzMCnYuhrCfxB"

# UPbit 객체 생성
upbit = pyupbit.Upbit(access, secret)

def get_start_time(ticker):
    """시장 시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(currency="KRW"):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == currency:
            return float(b['balance'])
    return 0.0

def get_current_price(ticker):
    """현재가 조회"""
    orderbook = pyupbit.get_orderbook(ticker)
    current_price = orderbook["orderbook_units"][0]["ask_price"]
    return current_price

def calculate_rsi(data, window=14):
    """RSI 계산"""
    diff = data.diff(1)
    gain = diff.where(diff > 0, 0).rolling(window=window).mean()
    loss = -diff.where(diff < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

bought_prices = {}  # 매수한 코인의 가격 저장 변수
banned_coins = {}  # 손절한 코인의 최종 시간 저장 변수
min_bid_amount = 5000  # 최소 구매 가능 금액

print("Autotrade start")
while True:
    try:
        now = datetime.datetime.now()
        total_balance = get_balance()  # 현재 보유 현금 조회

        # 코인 목록
        coins = ["KRW-BTC", "KRW-XRP", "KRW-ETC", "KRW-SC", "KRW-ETH", 
                 "KRW-DOGE", "KRW-CHZ", "KRW-LOOM", "KRW-MTL", "KRW-GLM",
                 "KRW-HUNT", "KRW-STX", "KRW-SOL", "KRW-MATIC",
                 "KRW-SAND", "KRW-HIVE", "KRW-FLOW", "KRW-IOTA", "KRW-BORA"]

        for coin in coins:
            if coin in bought_prices:  # 이미 매수한 코인은 건너뛰기
                # RSI 기반 매도 로직 추가
                df = pyupbit.get_ohlcv(coin, interval="minute60", count=14)
                rsi = calculate_rsi(df['close'])
                if rsi > 65:
                    balance = get_balance(coin.split('-')[1])
                    if balance > 0:
                        sell_result = upbit.sell_market_order(coin, balance)
                        if sell_result:
                            print(f"{coin} RSI 기반 매도 완료 - 매도 금액: {sell_result}")
                            del bought_prices[coin]
                continue

            df = pyupbit.get_ohlcv(coin, interval="minute60", count=14)
            current_price = get_current_price(coin)
            rsi = calculate_rsi(df['close'])

            # RSI가 35 미만이고 최소 구매 가능 금액 이상일 때 매수 진행
            if rsi < 35 and total_balance >= min_bid_amount:
                buying_amount = total_balance * 0.3  # 보유 현금의 30% 매수
                if buying_amount >= min_bid_amount:
                    buy_result = upbit.buy_market_order(coin, buying_amount)
                    if buy_result:
                        bought_prices[coin] = current_price
                        print(f"{coin} 매수 완료 - 매수 금액: {buying_amount}")

        time.sleep(60)  # 60초마다 반복
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(60)
