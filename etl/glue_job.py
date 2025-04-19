import sys
import boto3
import pandas as pd
from awsglue.utils import getResolvedOptions

# Define input args if used as a Glue Job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# S3 locations
raw_bucket = "predictive-inventory-data"
raw_prefix = "raw/"
clean_prefix = "clean/"

s3 = boto3.client('s3')

def list_s3_objects(bucket, prefix):
    """List all object keys under the specified S3 prefix."""
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.json')]

def process_file(key):
    """Read, transform, and write a single file."""
    obj = s3.get_object(Bucket=raw_bucket, Key=key)
    df = pd.read_json(obj['Body'])

    # Transformations
    df.drop(columns=['session_id'], inplace=True, errors='ignore')
    df.rename(columns={'sales_date': 'timestamp'}, inplace=True)

    # Save cleaned file
    clean_key = key.replace(raw_prefix, clean_prefix)
    output_buffer = df.to_json(orient='records', lines=True)
    s3.put_object(Bucket=raw_bucket, Key=clean_key, Body=output_buffer)

def main():
    raw_keys = list_s3_objects(raw_bucket, raw_prefix)
    for key in raw_keys:
        process_file(key)

if __name__ == "__main__":
    main()
