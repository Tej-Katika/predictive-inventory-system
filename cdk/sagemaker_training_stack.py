from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
)
from constructs import Construct

class SageMakerTrainingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, sagemaker_execution_role_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Lambda Function to Launch SageMaker Training Job
        training_lambda = _lambda.Function(
            self, "TriggerSageMakerTrainingLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("sagemaker_lambda"),  # We'll place the Lambda code here
            environment={
                "SAGEMAKER_EXECUTION_ROLE_ARN": sagemaker_execution_role_arn
            },
            timeout=Duration.minutes(5),
        )

        # 2. IAM Permissions for Lambda to Create Training Jobs
        # Attach both required permissions
        training_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "sagemaker:CreateTrainingJob",  
                    "iam:PassRole"                  
                ],
                resources=[
                    "arn:aws:sagemaker:us-east-1:515966531467:training-job/*",              
                    "arn:aws:iam::515966531467:role/SageMaker-training-for-lambda"           
                ]
            )
        )


        # 3. EventBridge Rule to Trigger Lambda (Daily 3 AM UTC)
        training_rule = events.Rule(
            self, "DailyTrainingSchedule",
            schedule=events.Schedule.cron(minute="0", hour="3")
        )

        training_rule.add_target(targets.LambdaFunction(training_lambda))
