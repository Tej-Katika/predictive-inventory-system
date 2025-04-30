#!/usr/bin/env python3

import aws_cdk as cdk

from cdk.predictive_inventory_stack import PredictiveInventoryStack
from sagemaker_training_stack import SageMakerTrainingStack

from aws_cdk import aws_ec2 as ec2

app = cdk.App()

# Inventory Pipeline Stack
PredictiveInventoryStack(app, "PredictiveInventoryStack")

# Provide your existing SageMaker Execution Role ARN
sagemaker_execution_role_arn = "arn:aws:iam::515966531467:role/SageMaker-training-for-lambda"

# SageMaker Training Stack
SageMakerTrainingStack(app, "SageMakerTrainingStack",
                       sagemaker_execution_role_arn=sagemaker_execution_role_arn)

app.synth()
