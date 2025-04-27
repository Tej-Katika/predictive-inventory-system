import sys
import boto3
import pandas as pd
import json
from datetime import datetime
from io import BytesIO
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ['JOB_NAME'])

# S3 Config
s3 = boto3.client('s3')
bucket = "cdkstack-inventorydatabucket1b7c2a3c-dsqfppsvh2hm"
aggregated_prefix = "aggregated/"
output_prefix = "deepar/"

# Step 1: List all aggregated files
response = s3.list_objects_v2(Bucket=bucket, Prefix=aggregated_prefix)
keys = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".csv")]

# Step 2: Load all CSVs into one DataFrame
all_data = []
for key in keys:
    obj = s3.get_object(Bucket=bucket, Key=key)
    content = obj['Body'].read()
    df = pd.read_csv(BytesIO(content))
    all_data.append(df)

if not all_data:
    print("No aggregated data found.")
    sys.exit()

df = pd.concat(all_data, ignore_index=True)
df["date"] = pd.to_datetime(df["date"])
df["department"] = df["department"].astype(str)

# Step 3: Pivot data to time series per department
grouped = df.groupby(["department", "date"]).sum().reset_index()
pivoted = grouped.pivot(index="date", columns="department", values="total_sales").fillna(0)
pivoted = pivoted.sort_index()

# Step 4: Create DeepAR format
train_data = []
test_data = []

forecast_horizon = 7

for department in pivoted.columns:
    target = pivoted[department].tolist()
    start_date = str(pivoted.index[0].date())

    if len(target) <= forecast_horizon:
        print(f"Skipping {department} – not enough data ({len(target)} days)")
        continue

    full_series = {
        "start": start_date,
        "target": target,
        "cat": [department]
    }

    train_series = {
        "start": start_date,
        "target": target[:-forecast_horizon],
        "cat": [department]
    }

    train_data.append(train_series)
    test_data.append(full_series)

# Step 5: Write to S3
def write_jsonl(data, s3_path):
    json_lines = "\n".join([json.dumps(rec) for rec in data])
    s3.put_object(Bucket=bucket, Key=s3_path, Body=json_lines.encode("utf-8"))
    print(f"Wrote {len(data)} series to {s3_path}")

write_jsonl(train_data, f"{output_prefix}train/train.json")
write_jsonl(test_data, f"{output_prefix}test/test.json")

print("DeepAR datasets generated successfully.")
