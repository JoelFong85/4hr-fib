from constants import TrendType
import pandas as pd


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
