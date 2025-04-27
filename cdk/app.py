import aws_cdk as cdk
from sagemaker_stack import SageMakerStudioStack

app = cdk.App()

SageMakerStudioStack(
    app, 
    "SageMakerStudioStack"
)

app.synth()
