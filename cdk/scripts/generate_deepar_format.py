import sys
import boto3
import pandas as pd
import json
from io import StringIO
from datetime import datetime
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# S3 setup
bucket = "cdkstack-inventorydatabucket1b7c2a3c-dsqfppsvh2hm"
source_prefix = "aggregated/"
train_prefix = "train/"
test_prefix = "test/"

s3 = boto3.client("s3")

def list_csv_keys(bucket, prefix):
    """List all .csv files under a prefix."""
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.csv')]

def load_data(keys):
    dfs = []
    for key in keys:
        obj = s3.get_object(Bucket=bucket, Key=key)
        csv_str = obj['Body'].read().decode('utf-8')
        df = pd.read_csv(StringIO(csv_str))
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def prepare_deepar_series(df):
    df['date'] = pd.to_datetime(df['date'])
    series = []

    for dept, group in df.groupby("department"):
        group = group.sort_values("date")
        start = group['date'].iloc[0].strftime("%Y-%m-%d %H:%M:%S")
        target = group['total_sales'].tolist()

        item = {
            "start": start,
            "cat": [dept],
            "target": target
        }

        # Split last 7 days as test set
        train_item = dict(item)
        train_item["target"] = target[:-7] if len(target) > 7 else target

        test_item = item

        series.append(("train", dept, train_item))
        series.append(("test", dept, test_item))
    
    return series

def write_to_s3(data):
    for split, dept, record in data:
        output_prefix = train_prefix if split == "train" else test_prefix
        key = f"{output_prefix}{dept.replace(' ', '_')}.json"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(record)
        )
        print(f"Written {key}")

def main():
    keys = list_csv_keys(bucket, source_prefix)
    if not keys:
        print("No input files found.")
        return

    df = load_data(keys)
    deepar_data = prepare_deepar_series(df)
    write_to_s3(deepar_data)

if __name__ == "__main__":
    main()
