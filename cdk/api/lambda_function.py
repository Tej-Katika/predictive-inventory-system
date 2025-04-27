import json
import boto3
import urllib3
import uuid
import time
from datetime import datetime

s3 = boto3.client('s3')
http = urllib3.PoolManager()

BUCKET_NAME = "cdkstack-inventorydatabucket1b7c2a3c-dsqfppsvh2hm"
KEY_PREFIX = "raw/"

def handler(event, context):
    for _ in range(3):  # Reduced to avoid rate limit
        try:
            response = http.request('GET', 'https://random-data-api.com/api/commerce/random_commerce')
            if response.status == 200:
                record = json.loads(response.data.decode("utf-8"))

                record["timestamp"] = datetime.utcnow().isoformat()
                record["product_id"] = str(uuid.uuid4())

                key = f"{KEY_PREFIX}record-{record['product_id']}.json"
                s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=json.dumps(record))

                print(f"Uploaded record to {key}")
            else:
                print(f"HTTP Error {response.status}: {response.data}")

        except Exception as e:
            print(f"Exception occurred: {str(e)}")

        time.sleep(0.5)  # Prevent 429 errors

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully ingested data from Random Data API')
    }
