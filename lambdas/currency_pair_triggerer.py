import boto3
import os
from datetime import datetime, timedelta, UTC
import json

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get("CURRENCY_PAIRS_TABLE_NAME", "CurrencyPairs")
if not table_name:
    raise Exception("CURRENCY_PAIRS_TABLE_NAME environment variable not set.")
table = dynamodb.Table(table_name)

sqs = boto3.client("sqs", region_name="ap-southeast-1")
queue_url = os.environ["FIB_ANALYSIS_LAMBDA_QUEUE_URL"]


def run(event, context):
    now = datetime.now(UTC)
    threshold_time = now - timedelta(hours=3.5)

    response = table.scan()
    items = response.get("Items", [])

    eligible_pairs = []

    for item in items:
        if (
                not item.get("enabled", True)
                or "last_triggered" not in item
        ):
            continue

        try:
            last_triggered_time = datetime.fromisoformat(item["last_triggered"])
        except Exception as e:
            print(f"currency_pair_triggerer: Skipping {item['pair']} due to invalid datetime: {e}")
            continue

        if last_triggered_time < threshold_time:
            eligible_pairs.append(item["pair"])

    if not eligible_pairs:
        rounded_now = now.replace(minute=0, second=0, microsecond=0)
        formatted_time = rounded_now.strftime("%d-%m-%Y %H:%M")

        print(f"currency_pair_triggerer: No eligible pairs found at {formatted_time} — exiting.")
        # TODO: Send telegram alert if no pairs found
        return

    print(f"currency_pair_triggerer: Dispatching {len(eligible_pairs)} pairs to SQS.")

    for pair in eligible_pairs:
        print(f"currency_pair_triggerer: Sending {pair}.")
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps({"pair": pair})
        )

    print(f"currency_pair_triggerer: All eligible pairs sent to SQS.")
