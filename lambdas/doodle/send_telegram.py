import boto3
import os
import requests
import base64

s3 = boto3.client('s3')
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

def main(event, context):
    for record in event['Records']:
        new_image = record['dynamodb']['NewImage']
        if new_image['status']['S'] != 'READY':
            continue

        pair = new_image['pair']['S']
        s3_key = new_image['s3_key']['S']
        bucket = os.environ['S3_BUCKET']

        obj = s3.get_object(Bucket=bucket, Key=s3_key)
        img_bytes = obj['Body'].read()

        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': img_bytes}
        data = {'chat_id': CHAT_ID, 'caption': f"Trade Setup for {pair}"}
        requests.post(telegram_url, data=data, files=files)