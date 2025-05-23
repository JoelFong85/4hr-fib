from api import fetch_candlestick_data, get_latest_candle
from technical_analysis import calculate_ema, identify_trends, merge_consecutive_trends, find_fib_crosses

from dotenv import load_dotenv

load_dotenv()

MAX_LIST_LENGTH = 4
FIB_LEVEL_TO_TEST = 61.8


def analyse_pair(currency_pair):
    try:
        df = fetch_candlestick_data(currency_pair, granularity="H4", count=200)

        df = calculate_ema(df)

        trends_df = identify_trends(df)

        merged_trends_df = merge_consecutive_trends(trends_df)

        print(f'===== analyse_pair: merged trends for {currency_pair} =====')
        print(merged_trends_df)

        fib_cross_list = find_fib_crosses(
            merged_trends_df,
            current_candle=get_latest_candle(df),
            max_list_length=MAX_LIST_LENGTH,
            fib_level=FIB_LEVEL_TO_TEST)

        print('===== analyse_pair: fib cross list =====')
        print(fib_cross_list)

        return True

    except Exception as e:
        print(f"analyse_pair: Error analysing {currency_pair}: {e}")
        return False


if __name__ == "__main__":
    currency_pair = "CAD_JPY"  # Change when testing locally
    analyse_pair(currency_pair)
