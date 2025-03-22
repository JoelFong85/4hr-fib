import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import pandas as pd
import ta
from constants.trend_types import TrendType
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OANDA_API_KEY")
if not API_KEY:
    raise ValueError("Missing OANDA API Key. Make sure to set OANDA_API_KEY in your .env file.")

INSTRUMENT = "AUD_CHF"  # Change this to the forex pair you want

client = oandapyV20.API(access_token=API_KEY)


def fetch_candlestick_data(instrument, granularity="H4", count=200):
    params = {"count": count, "granularity": granularity}
    r = instruments.InstrumentsCandles(instrument=instrument, params=params)
    client.request(r)

    candles = r.response['candles']

    df = pd.DataFrame([
        {
            "timestamp": c["time"],
            "open": float(c["mid"]["o"]),
            "high": float(c["mid"]["h"]),
            "low": float(c["mid"]["l"]),
            "close": float(c["mid"]["c"])
        }
        for c in candles if c["complete"]
    ])

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


def calculate_ema(df, period=15):
    df["ema_15"] = ta.trend.ema_indicator(df["close"], window=period)
    return df


def identify_trends(df):
    trend_list = []
    latest_trend = None
    candle_count = 0
    max_swing_price = None
    max_swing_price_time = None
    start_time = None

    def append_trend(end_index):
        trend_list.append({
            "trend": latest_trend,
            "start_time": start_time,
            "end_time": df["timestamp"].iloc[end_index],
            "max_swing_price": max_swing_price,
            "max_swing_price_time": max_swing_price_time,
            "candle_count": candle_count
        })

    for i in range(len(df)):
        open_price = df["open"].iloc[i]
        close_price = df["close"].iloc[i]
        high_price = df["high"].iloc[i]
        low_price = df["low"].iloc[i]
        ema_price = df["ema_15"].iloc[i]
        timestamp = df["timestamp"].iloc[i]

        # print("==========")
        # print(f"current index: {i + 1}")
        # print(f"candle count: {candle_count}")
        # print(f"trend list count {len(trend_list)}")
        # print(f"Timestamp: {timestamp}, Open: {open_price}, Close: {close_price}, EMA(15): {ema_price}")

        # Determine current trend
        if open_price >= ema_price and close_price >= ema_price:
            current_trend = TrendType.UPTREND.value
        elif open_price <= ema_price and close_price <= ema_price:
            current_trend = TrendType.DOWNTREND.value
        else:
            if latest_trend is not None:
                append_trend(i - 1)
            candle_count = 0
            latest_trend = None
            continue  # Skip to next candle

        if latest_trend == current_trend:
            candle_count += 1

            # Update max swing price
            if latest_trend == TrendType.UPTREND.value:
                if max_swing_price is None or high_price > max_swing_price:
                    max_swing_price = high_price
                    max_swing_price_time = timestamp
            elif latest_trend == TrendType.DOWNTREND.value:
                if max_swing_price is None or low_price < max_swing_price:
                    max_swing_price = low_price
                    max_swing_price_time = timestamp

        else:
            # If a new trend starts, add the previous one (if it exists)
            if latest_trend is not None:
                append_trend(i - 1)

            # Start a new trend
            latest_trend = current_trend
            start_time = timestamp
            candle_count = 1
            max_swing_price = high_price if current_trend == "uptrend" else low_price
            max_swing_price_time = timestamp

    # Append last trend after loop
    if latest_trend is not None:
        append_trend(len(df) - 1)

    df_trends = pd.DataFrame(trend_list)

    # Remove trends with less than 3 candles
    df_trends = df_trends[df_trends["candle_count"] >= 3]

    # Format timestamps
    time_columns = ["start_time", "end_time", "max_swing_price_time"]
    for col in time_columns:
        df_trends[col] = pd.to_datetime(df_trends[col]).dt.strftime("%d-%m-%y %H:%M")

    return df_trends


def merge_consecutive_trends(df_trends):
    if len(df_trends) <= 1:
        return df_trends

    merged_list = []
    tracked_trend = df_trends.iloc[0].copy()

    for i in range(1, len(df_trends)):
        current = df_trends.iloc[i]

        if current["trend"] == tracked_trend["trend"]:
            tracked_trend["end_time"] = current["end_time"]
            tracked_trend["candle_count"] += current["candle_count"]

            if (
                    (tracked_trend["trend"] == TrendType.UPTREND.value
                     and
                     float(current["max_swing_price"]) > float(tracked_trend["max_swing_price"]))
                    or
                    (tracked_trend["trend"] == TrendType.DOWNTREND.value
                     and
                     float(current["max_swing_price"]) < float(tracked_trend["max_swing_price"]))
            ):
                tracked_trend["max_swing_price"] = current["max_swing_price"]
                tracked_trend["max_swing_price_time"] = current["max_swing_price_time"]

        else:
            merged_list.append(tracked_trend)
            tracked_trend = current.copy()

    merged_list.append(tracked_trend)
    return pd.DataFrame(merged_list).reset_index(drop=True)


def main():
    df = fetch_candlestick_data(INSTRUMENT, granularity="H4", count=200)

    df = calculate_ema(df)

    trends_df = identify_trends(df)

    merged_trends_df = merge_consecutive_trends(trends_df)

    print(merged_trends_df)


if __name__ == "__main__":
    main()
