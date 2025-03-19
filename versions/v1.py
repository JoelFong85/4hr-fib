# First proper version
# Issues:
# - includes even single candles, giving a lot of white noise
# - includes candles whose bodies are intersecting with EMA line. Bodies have to be either above or below EMA line


import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import pandas as pd
import ta

# OANDA API Credentials (Replace with your credentials)
API_KEY = ""
INSTRUMENT = "AUD_CHF"  # Change this to the forex pair you want

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


# Function to identify trends
def identify_trends(df):
    trends = []
    current_trend = None
    start_time = None
    highest_price = None
    lowest_price = None
    highest_time = None
    lowest_time = None

    for i in range(len(df)):
        candle_above_ema = df["close"].iloc[i] > df["ema_15"].iloc[i]

        if current_trend is None:
            current_trend = "uptrend" if candle_above_ema else "downtrend"
            start_time = df["timestamp"].iloc[i]
            highest_price = df["high"].iloc[i]
            lowest_price = df["low"].iloc[i]
            highest_time = start_time
            lowest_time = start_time
        else:
            new_trend = "uptrend" if candle_above_ema else "downtrend"

            if new_trend != current_trend:
                trends.append({
                    "trend": current_trend,
                    "start_time": start_time,
                    "end_time": df["timestamp"].iloc[i - 1],
                    "highest_price": highest_price,
                    "highest_time": highest_time,
                    "lowest_price": lowest_price,
                    "lowest_time": lowest_time
                })

                current_trend = new_trend
                start_time = df["timestamp"].iloc[i]
                highest_price = df["high"].iloc[i]
                lowest_price = df["low"].iloc[i]
                highest_time = start_time
                lowest_time = start_time
            else:
                if df["high"].iloc[i] > highest_price:
                    highest_price = df["high"].iloc[i]
                    highest_time = df["timestamp"].iloc[i]

                if df["low"].iloc[i] < lowest_price:
                    lowest_price = df["low"].iloc[i]
                    lowest_time = df["timestamp"].iloc[i]

    if current_trend is not None:
        trends.append({
            "trend": current_trend,
            "start_time": start_time,
            "end_time": df["timestamp"].iloc[-1],
            "highest_price": highest_price,
            "highest_time": highest_time,
            "lowest_price": lowest_price,
            "lowest_time": lowest_time
        })

    df_trends = pd.DataFrame(trends)

    # Format date and time as 'dd-MM-yy HH:mm'
    time_columns = ["start_time", "end_time", "highest_time", "lowest_time"]
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
