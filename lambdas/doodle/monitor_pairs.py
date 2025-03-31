import json
import boto3
import os

sqs = boto3.client('sqs')
QUEUE_URL = os.environ['QUEUE_URL']
PAIRS = ['EUR/USD', 'USD/JPY', 'GBP/USD']  # Add all your pairs

def main(event, context):
    for pair in PAIRS:
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps({'pair': pair})
        )
    return {"status": "messages sent"}