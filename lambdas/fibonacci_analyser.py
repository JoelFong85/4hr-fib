import os
import json
from strategies.four_hr.main import analyse_pair
from datetime import datetime, UTC
import boto3

dynamodb = boto3.resource("dynamodb")
table_name = os.environ["CURRENCY_PAIRS_TABLE_NAME"]
table = dynamodb.Table(table_name)


def run(event, context):
    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            pair = body.get("pair")

            if not pair:
                print("fibonacci_analyser: No 'pair' found in message body")
                raise ValueError("No 'pair' found in message body")

            print(f"fibonacci_analyser: Running analysis for: {pair}")

            success = analyse_pair(pair)

            if success:
                now = datetime.now(UTC).isoformat()
                table.update_item(
                    Key={"pair": pair},
                    UpdateExpression="SET last_triggered = :ts",
                    ExpressionAttributeValues={":ts": now}
                )
                print(f"fibonacci_analyser: Updated last_triggered for {pair} at {now}")
            else:
                print(f"fibonacci_analyser: Analysis failed for {pair}, not updating timestamp")

        except Exception as e:
            print(f"fibonacci_analyser: Error processing message: {e}")
