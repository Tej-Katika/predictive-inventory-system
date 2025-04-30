import os
import sagemaker
from sagemaker.estimator import Estimator

def lambda_handler(event, context):
    # Initialize SageMaker session and retrieve execution role
    sagemaker_session = sagemaker.Session()
    region = sagemaker_session.boto_region_name
    role_arn = os.environ['SAGEMAKER_EXECUTION_ROLE_ARN']

    # Retrieve the official DeepAR image URI from SageMaker SDK
    image_uri = sagemaker.image_uris.retrieve(
        framework='forecasting-deepar',
        region=region
    )

    # Define output and input S3 paths (update these as needed)
    bucket = sagemaker_session.default_bucket()
    input_s3_uri = f's3://cdkstack-inventorydatabucket1b7c2a3c-dsqfppsvh2hm/deepar/train/train.json'
    output_s3_uri = f's3://cdkstack-inventorydatabucket1b7c2a3c-dsqfppsvh2hm/deepar/'

    # Configure the estimator for DeepAR training
    estimator = Estimator(
        image_uri=image_uri,
        role=role_arn,
        instance_count=1,
        instance_type='ml.m5.large',
        volume_size=10,  # GB
        max_run=3600,  # 1 hour
        input_mode='File',
        output_path=output_s3_uri,
        sagemaker_session=sagemaker_session
    )

    # Start training job
    estimator.fit({'train': input_s3_uri})

    return {
        'statusCode': 200,
        'body': f'Training job for DeepAR started successfully. Input: {input_s3_uri}, Output: {output_s3_uri}'
    }
