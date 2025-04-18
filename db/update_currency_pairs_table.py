# Run ```AWS_PROFILE=fib-trading-bot python db/update_currency_pairs_table.py``` in terminal

import boto3
import os

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get("CURRENCY_PAIRS_TABLE_NAME", "CurrencyPairs")
if not table_name:
    raise Exception("CURRENCY_PAIRS_TABLE_NAME environment variable not set.")
table = dynamodb.Table(table_name)

# List of pairs to patch (you can hardcode or scan if needed)
pairs = [
    "AUD/CAD",
    "AUD/CHF",
    "AUD/JPY",
    "AUD/NZD",
    "AUD/USD",
    "CAD/CHF",
    # "CAD/JPY",
    "CHF/JPY",
    "EUR/AUD",
    "EUR/CAD",
    "EUR/CHF",
    "EUR/GBP",
    "EUR/JPY",
    "EUR/NZD",
    "EUR/USD",
    "GBP/AUD",
    "GBP/CAD",
    "GBP/CHF",
    "GBP/JPY",
    "GBP/NZD",
    "GBP/USD",
    "NZD/CAD",
    "NZD/CHF",
    "NZD/JPY",
    "NZD/USD",
    "USD/CAD",
    "USD/CHF",
    "USD/JPY",
]

for pair in pairs:
    response = table.update_item(
        Key={'pair': pair},
        UpdateExpression="SET enabled = :false",
        ExpressionAttributeValues={':false': False}
    )
    print(f"Updated {pair}: enabled=False")

print("All currency pairs disabled.")
