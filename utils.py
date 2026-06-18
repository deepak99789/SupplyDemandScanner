import pandas as pd


def candle_body(row):
    return abs(row["Close"] - row["Open"])


def candle_range(row):
    return row["High"] - row["Low"]


def is_bullish(row):
    return row["Close"] > row["Open"]


def is_bearish(row):
    return row["Close"] < row["Open"]


def calculate_atr(df, period=14):

    high = df["High"]
    low = df["Low"]
    close = df["Close"].shift()

    tr = pd.concat([
        high - low,
        (high - close).abs(),
        (low - close).abs()
    ], axis=1).max(axis=1)

    return tr.rolling(period).mean()


def body_ratio(row):

    rng = candle_range(row)

    if rng == 0:
        return 0

    return candle_body(row) / rng


def risk_reward(proximal, distal, rr=2):

    risk = abs(proximal - distal)

    if proximal > distal:

        target = proximal + risk * rr

    else:

        target = proximal - risk * rr

    return round(target, 5)
