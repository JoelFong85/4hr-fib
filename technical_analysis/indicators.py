import ta


def calculate_ema(df, period=15):
    df["ema_15"] = ta.trend.ema_indicator(df["close"], window=period)
    return df
