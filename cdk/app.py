import os
import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2

from vpc_stack.vpc_stack import VPCStack
from sagemaker_stack.sagemaker_stack import SageMakerStudioStack

app = cdk.App()

# 1. Create VPC first
vpc_stack = VPCStack(
    app, "VPCStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION")
    )
)

# 2. Then pass VPC into SageMaker Studio Stack
sagemaker_stack = SageMakerStudioStack(
    app, "SageMakerStudioStack",
    vpc=vpc_stack.vpc,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION")
    )
)

app.synth()