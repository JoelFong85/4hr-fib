# Run ```AWS_PROFILE=fib-trading-bot python db/seed_currency_pairs_table.py``` in terminal to seed data

import boto3
from datetime import datetime, UTC
import os

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get("CURRENCY_PAIRS_TABLE_NAME", "CurrencyPairs")
if not table_name:
    raise Exception("CURRENCY_PAIRS_TABLE_NAME environment variable not set.")
table = dynamodb.Table(table_name)

pairs = [
    "AUD/CAD",
    "AUD/CHF",
    "AUD/JPY",
    "AUD/NZD",
    "AUD/USD",
    "CAD/CHF",
    "CAD/JPY",
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

now = datetime.now(UTC).isoformat()

for pair in pairs:
    table.put_item(Item={
        'pair': pair,
        'last_triggered': now,
        'created_at': now,
        'enabled': True,
        'notes': ''
    })

print("Currency pair records added.")
