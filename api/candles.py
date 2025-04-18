import os
import boto3
import json
from dotenv import load_dotenv
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import pandas as pd

load_dotenv()


def get_api_key():
    # Try retrieving from local env
    API_KEY = os.getenv("OANDA_API_KEY")
    if API_KEY:
        return API_KEY

    # Else fetch from AWS Secrets Manager (for Lambda)
    secret_name = "fib-trading-bot/oanda"
    region = os.getenv("AWS_REGION", "ap-southeast-1")

    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])

    return secret["OANDA_API_KEY"]


API_KEY = get_api_key()

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
