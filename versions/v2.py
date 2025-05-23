# Fixed issues from v1
# - removing single candles from being counted in a trend
# - removed candles whose bodies are intersecting with EMA line

import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import pandas as pd
import ta
from constants.trend_types import TrendType

# OANDA API Credentials (Replace with your credentials)
API_KEY = ""
INSTRUMENT = "AUD_CHF"

# Initialize OANDA API Client
client = oandapyV20.API(access_token=API_KEY)


# Function to fetch OHLCV data from OANDA
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


# Function to calculate 15-period EMA
def calculate_ema(df, period=15):
    df["ema_15"] = ta.trend.ema_indicator(df["close"], window=period)
    return df


# Function to identify trends with a minimum of 3 consecutive candles
def identify_trends(df):
    trend_list = []
    latest_trend = None
    candle_count = 0
    max_swing_price = None
    max_swing_price_time = None
    start_time = None

    for i in range(len(df)):
        open_price = df["open"].iloc[i]
        close_price = df["close"].iloc[i]
        ema_price = df["ema_15"].iloc[i]
        timestamp = df["timestamp"].iloc[i]

        # print("==========")
        # print(f"current index: {i + 1}")
        # print(f"candle count: {candle_count}")
        # print(f"trend list count {len(trend_list)}")
        print(f"Timestamp: {timestamp}, Open: {open_price}, Close: {close_price}, EMA(15): {ema_price}")

        # Determine current trend
        if open_price >= ema_price and close_price >= ema_price:
            # print("uptrend")
            current_trend = TrendType.UPTREND.value
        elif open_price <= ema_price and close_price <= ema_price:
            # print("downtrend")
            current_trend = TrendType.DOWNTREND.value
        else:
            # print("no trend")
            if latest_trend is not None:
                trend_list.append({
                    "trend": latest_trend,
                    "start_time": start_time,
                    "end_time": df["timestamp"].iloc[i - 1],
                    "max_swing_price": max_swing_price,
                    "max_swing_price_time": max_swing_price_time,
                    "candle_count": candle_count
                })
            candle_count = 0
            latest_trend = None
            continue  # Skip to next candle

        if latest_trend == current_trend:
            # print("latest_trend == current_trend")
            candle_count += 1

            # Update max swing price
            if latest_trend == TrendType.UPTREND.value:
                # Joel comment - use high price instead of close price
                if max_swing_price is None or close_price > max_swing_price:
                    max_swing_price = close_price
                    max_swing_price_time = timestamp
            elif latest_trend == TrendType.DOWNTREND.value:
                # Joel comment - use low price instead of close price
                if max_swing_price is None or close_price < max_swing_price:
                    max_swing_price = close_price
                    max_swing_price_time = timestamp

        else:
            # print("latest_trend != current_trend")
            # If a new trend starts, add the previous one (if it exists)
            if latest_trend is not None:
                # print("Appending trend")
                trend_list.append({
                    "trend": latest_trend,
                    "start_time": start_time,
                    "end_time": df["timestamp"].iloc[i - 1],
                    "max_swing_price": max_swing_price,
                    "max_swing_price_time": max_swing_price_time,
                    "candle_count": candle_count
                })

            # Start a new trend
            latest_trend = current_trend
            start_time = timestamp
            candle_count = 1
            max_swing_price = close_price  # Joel comment - this should be high price for uptrend / low price for downtrend
            max_swing_price_time = timestamp

    # Append last trend after loop
    if latest_trend is not None:
        # print("Append last trend after loop")
        trend_list.append({
            "trend": latest_trend,
            "start_time": start_time,
            "end_time": df["timestamp"].iloc[-1],
            "max_swing_price": max_swing_price,
            "max_swing_price_time": max_swing_price_time,
            "candle_count": candle_count
        })

    # Convert to DataFrame
    df_trends = pd.DataFrame(trend_list)

    # Remove trends with less than 3 candles
    df_trends = df_trends[df_trends["candle_count"] >= 3]

    # Format timestamps
    time_columns = ["start_time", "end_time", "max_swing_price_time"]
    for col in time_columns:
        df_trends[col] = pd.to_datetime(df_trends[col]).dt.strftime("%d-%m-%y %H:%M")

    return df_trends


# Main function
def main():
    # print(f"Fetching data for {INSTRUMENT}...")
    df = fetch_candlestick_data(INSTRUMENT, granularity="H4", count=200)

    # print("Calculating EMA...")
    df = calculate_ema(df)

    # print("Identifying trends...")
    trends_df = identify_trends(df)

    # print("\nIdentified Trends:")
    print(trends_df)


if __name__ == "__main__":
    main()
