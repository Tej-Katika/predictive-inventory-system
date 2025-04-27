import sys
import boto3
import pandas as pd
from io import BytesIO
from awsglue.utils import getResolvedOptions
from datetime import datetime

# Step 0: Get job arguments
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# Step 1: Setup S3 client and configuration
s3 = boto3.client('s3')
bucket = "cdkstack-inventorydatabucket1b7c2a3c-dsqfppsvh2hm"
clean_prefix = "clean/"
aggregated_prefix = "aggregated/"

def log(msg):
    print(f"[Glue ETL] {msg}")

# Step 2: List JSON files in clean/ folder
response = s3.list_objects_v2(Bucket=bucket, Prefix=clean_prefix)
keys = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.json')]

log(f"Found {len(keys)} files in {clean_prefix}")

if not keys:
    log("No files found. Exiting.")
    sys.exit(0)

# Step 3: Load and concatenate all JSON records
all_records = []
for key in keys:
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        content = obj['Body'].read()
        df = pd.read_json(BytesIO(content), lines=True)
        all_records.append(df)
    except Exception as e:
        log(f"Failed to process {key}: {e}")

if not all_records:
    log("No valid records to process.")
    sys.exit(0)

full_df = pd.concat(all_records, ignore_index=True)

# Step 4: Timestamp normalization and grouping
full_df['timestamp'] = pd.to_datetime(full_df['timestamp'], utc=True, errors='coerce')
full_df['date'] = full_df['timestamp'].dt.date

grouped = (
    full_df.groupby(['date', 'department'])
           .agg({'price_numeric': 'sum'})
           .reset_index()
           .rename(columns={'price_numeric': 'total_sales'})
)

log(f"Writing {len(grouped)} aggregated files to S3...")

# Step 5: Write CSV per day per department
for _, row in grouped.iterrows():
    try:
        output_key = f"{aggregated_prefix}{row['department'].replace(' ', '_')}/{row['date']}.csv"
        csv_data = row.to_frame().T.to_csv(index=False)
        s3.put_object(Bucket=bucket, Key=output_key, Body=csv_data)
        log(f"Written: {output_key}")
    except Exception as e:
        log(f"Failed to write {output_key}: {e}")

log("Aggregation complete.")
