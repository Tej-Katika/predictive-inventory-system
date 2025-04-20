import sys
import boto3
import pandas as pd
from awsglue.utils import getResolvedOptions

# Get job parameters passed via CDK
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'BUCKET_NAME'])

# Use bucket from arguments
raw_bucket = args['BUCKET_NAME']
raw_prefix = "raw/"
clean_prefix = "clean/"

s3 = boto3.client('s3')

def list_s3_objects(bucket, prefix):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.json')]

def process_file(key):
    obj = s3.get_object(Bucket=raw_bucket, Key=key)
    df = pd.read_json(obj['Body'])

    # Basic transformation
    df.drop(columns=['session_id'], inplace=True, errors='ignore')
    df.rename(columns={'sales_date': 'timestamp'}, inplace=True)

    output_buffer = df.to_json(orient='records', lines=True)
    s3.put_object(Bucket=raw_bucket, Key=key.replace(raw_prefix, clean_prefix), Body=output_buffer)

def main():
    raw_keys = list_s3_objects(raw_bucket, raw_prefix)
    for key in raw_keys:
        process_file(key)

if __name__ == "__main__":
    main()
