import yfinance as yf
import pandas as pd

# ===============================
# Timeframe Mapping
# ===============================

INTERVAL_MAP = {
    "1m": "1m",
    "2m": "2m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "60m": "60m",
    "90m": "90m",
    "1h": "60m",
    "4h": "1h",      # Later resample
    "1d": "1d",
    "1wk": "1wk",
    "1mo": "1mo"
}

# ===============================
# Download Data
# ===============================

def download_data(symbol, timeframe="1h", bars=500):

    interval = INTERVAL_MAP.get(timeframe, "60m")

    period = "730d"

    try:

        df = yf.download(
            symbol,
            interval=interval,
            period=period,
            progress=False,
            auto_adjust=False
        )

    except Exception:

        return None

    if df is None or len(df) == 0:
        return None

    df = df.tail(bars)

    df = df.rename(columns={
        "Open":"Open",
        "High":"High",
        "Low":"Low",
        "Close":"Close",
        "Volume":"Volume"
    })

    df = df[["Open","High","Low","Close","Volume"]]

    df.dropna(inplace=True)

    return df

FOREX_SYMBOLS = [

"EURUSD=X",
"GBPUSD=X",
"USDJPY=X",
"AUDUSD=X",
"NZDUSD=X",
"USDCAD=X",
"USDCHF=X",

"EURGBP=X",
"EURJPY=X",
"GBPJPY=X",

"GBPAUD=X",
"GBPCAD=X",

"AUDJPY=X",

"CADJPY=X"

]

CRYPTO_SYMBOLS = [

"BTC-USD",
"ETH-USD",
"SOL-USD",
"BNB-USD",
"XRP-USD",
"DOGE-USD",
"ADA-USD",
"AVAX-USD",
"LINK-USD"

]

COMMODITY_SYMBOLS = [

"GC=F",
"SI=F",
"CL=F",
"NG=F",
"HG=F"

]
US_STOCKS = [

"AAPL",
"MSFT",
"NVDA",
"META",
"AMZN",
"GOOG",
"TSLA",
"NFLX",
"AMD",
"INTC"

]
NSE_STOCKS = [

"RELIANCE.NS",
"TCS.NS",
"HDFCBANK.NS",
"ICICIBANK.NS",
"SBIN.NS",
"INFY.NS",
"ITC.NS",
"LT.NS",
"AXISBANK.NS",
"BAJFINANCE.NS"

]

def get_market_symbols(market):

    if market == "Forex":
        return FOREX_SYMBOLS

    elif market == "Crypto":
        return CRYPTO_SYMBOLS

    elif market == "Commodity":
        return COMMODITY_SYMBOLS

    elif market == "US Stocks":
        return US_STOCKS

    elif market == "NSE":
        return NSE_STOCKS

    return []

def load_market_data(
        market,
        timeframe,
        bars
):

    symbols = get_market_symbols(market)

    output = {}

    for symbol in symbols:

        df = download_data(
            symbol,
            timeframe,
            bars
        )

        if df is None:
            continue

        output[symbol] = df

    return output

