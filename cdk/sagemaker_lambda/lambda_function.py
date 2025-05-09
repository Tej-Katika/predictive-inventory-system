import os
import sagemaker
from sagemaker.estimator import Estimator

def lambda_handler(event, context):
    sagemaker_session = sagemaker.Session()
    region = sagemaker_session.boto_region_name
    role_arn = os.environ['SAGEMAKER_EXECUTION_ROLE_ARN']

    image_uri = sagemaker.image_uris.retrieve(
        framework='forecasting-deepar',
        region=region
    )

    input_s3_uri = 's3://cdkstack-inventorydatabucket1b7c2a3c-dsqfppsvh2hm/deepar/train/train.json'
    output_s3_uri = 's3://cdkstack-inventorydatabucket1b7c2a3c-dsqfppsvh2hm/deepar/output/'

    estimator = Estimator(
        image_uri=image_uri,
        role=role_arn,
        instance_count=1,
        instance_type='ml.m5.large',
        volume_size=10,
        max_run=3600,
        input_mode='File',
        output_path=output_s3_uri,
        sagemaker_session=sagemaker_session
    )

    estimator.fit({'train': input_s3_uri})

    return {
        'statusCode': 200,
        'body': 'Training job started.'
    }
