# Improvements since v3
# - calculation of whether most recent candle crossed the 75% fib levels of any swing high / low pairs

# Things to improve for v4
# - re-organise code into proper modules / classes
# - remove MAX_LIST_LENGTH, just do comparison of all peaks / valleys


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

# Variables to change
INSTRUMENT = "CAD_JPY"
MAX_LIST_LENGTH = 4
FIB_LEVEL_TO_TEST = 61.8

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


def get_latest_candle(df, n=1):
    return df.iloc[-n].to_dict()


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


def get_recent_swing_lists(merged_trends_df, max_list_length=3):
    swing_high_list = []
    swing_low_list = []

    # Iterate from the most recent trend backwards because we want to compare the latest swing highs/lows to the most recent candle
    for _, record in reversed(list(merged_trends_df.iterrows())):
        if record["trend"] == TrendType.UPTREND.value and len(swing_high_list) < max_list_length:
            swing_high_list.append(record)
        elif record["trend"] == TrendType.DOWNTREND.value and len(swing_low_list) < max_list_length:
            swing_low_list.append(record)

        # Stop early if we have enough in both lists
        if len(swing_high_list) >= max_list_length and len(swing_low_list) >= max_list_length:
            break

    return swing_high_list, swing_low_list


def calculate_fib_level(high_price, low_price, direction, fib_level):
    if direction == "up":
        return high_price - (fib_level / 100) * (high_price - low_price)
    else:
        return low_price + (fib_level / 100) * (high_price - low_price)


def check_latest_candle_crosses_fib_level(candle, fib_price):
    return candle['low'] <= fib_price <= candle['high']


def find_fib_crosses(merged_trends_df, current_candle, max_list_length=3, fib_level=75):
    swing_high_list, swing_low_list = get_recent_swing_lists(merged_trends_df, max_list_length)

    latest_trend = merged_trends_df.iloc[-1]["trend"]

    matched_pairs = []

    if latest_trend == TrendType.UPTREND.value:
        outer, inner = swing_high_list, swing_low_list
    else:
        outer, inner = swing_low_list, swing_high_list

    for outer_swing_level in outer:
        for inner_swing_level in inner:
            if pd.to_datetime(outer_swing_level["max_swing_price_time"]) < pd.to_datetime(
                    inner_swing_level["max_swing_price_time"]):
                first = outer_swing_level
                second = inner_swing_level
            else:
                first = inner_swing_level
                second = outer_swing_level

            # Determine direction
            if first["max_swing_price"] < second["max_swing_price"]:
                direction = "up"
                low = first
                high = second
            else:
                direction = "down"
                high = first
                low = second

            calculated_fib_level = calculate_fib_level(high["max_swing_price"], low["max_swing_price"], direction,
                                                       fib_level)

            if check_latest_candle_crosses_fib_level(current_candle, calculated_fib_level):
                matched_pairs.append({
                    "high_time": high["max_swing_price_time"],
                    "high_price": high["max_swing_price"],
                    "low_time": low["max_swing_price_time"],
                    "low_price": low["max_swing_price"],
                    f"fib_{fib_level}": calculated_fib_level
                })

    return matched_pairs


def main():
    df = fetch_candlestick_data(INSTRUMENT, granularity="H4", count=200)

    df = calculate_ema(df)

    trends_df = identify_trends(df)

    merged_trends_df = merge_consecutive_trends(trends_df)
    # print('===== merged trends =====')
    # print(merged_trends_df)

    fib_cross_list = find_fib_crosses(merged_trends_df, current_candle=get_latest_candle(df),
                                      max_list_length=MAX_LIST_LENGTH,
                                      fib_level=FIB_LEVEL_TO_TEST)
    print('===== fib cross list =====')
    print(fib_cross_list)


if __name__ == "__main__":
    main()
