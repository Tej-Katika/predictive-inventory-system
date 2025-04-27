from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_s3 as s3,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_glue as glue,
    CfnOutput
)
from constructs import Construct

class PredictiveInventoryStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. S3 Bucket
        data_bucket = s3.Bucket(
            self, "InventoryDataBucket",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
        from aws_cdk.aws_s3_deployment import BucketDeployment, Source
        BucketDeployment(
            self, "DeployGlueScript",
            sources=[Source.asset("./scripts")],
            destination_bucket=data_bucket,
            destination_key_prefix="scripts/"
        )

        # 2. Lambda
        ingestion_lambda = _lambda.Function(
            self, "IngestionLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.handler",
            code=_lambda.Code.from_asset("api"),
            environment={"BUCKET_NAME": data_bucket.bucket_name},
            timeout=Duration.seconds(10),
        )

        # 3. Grant S3 write to Lambda
        data_bucket.grant_put(ingestion_lambda)

        # EventBridge Rule to Trigger Lambda Every Hour
        hourly_lambda_rule = events.Rule(
            self, "HourlyIngestionTrigger",
            schedule=events.Schedule.rate(Duration.hours(1))
        )

        hourly_lambda_rule.add_target(
            targets.LambdaFunction(handler=ingestion_lambda)
        )

        # 4. API Gateway
        api = apigateway.LambdaRestApi(
            self, "InventoryIngestionAPI",
            handler=ingestion_lambda,
            proxy=True,
            deploy_options=apigateway.StageOptions(stage_name="prod")
        )

        # 5. IAM Role for Glue
        glue_role = iam.Role(
            self, "GlueJobRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
            ]
        )

        # 6. Glue Job (ETL)
        glue_job = glue.CfnJob(
            self, "InventoryGlueJobV4",
            name="InventoryETLJobV4",
            role=glue_role.role_arn,
            command={
                "name": "glueetl",
                "pythonVersion": "3",
                "scriptLocation": f"s3://{data_bucket.bucket_name}/scripts/glue_job.py"
            },
            glue_version="4.0",
            number_of_workers=2,
            worker_type="G.1X",
            execution_property=glue.CfnJob.ExecutionPropertyProperty(
                max_concurrent_runs=1
            ),
            default_arguments={
                "--job-language": "python",
                "--enable-metrics": "true",
                "--BUCKET_NAME": data_bucket.bucket_name
            }
        )

        # 7. EventBridge Rule (2 AM UTC) to Trigger ETL Job
        schedule_rule = events.Rule(
            self, "DailyGlueJobScheduleV4",
            schedule=events.Schedule.cron(minute="0", hour="2")
        )

        # 8. Add Glue ETL job as target using AwsApi
        schedule_rule.add_target(
            targets.AwsApi(
                service="Glue",
                action="startJobRun",
                parameters={"JobName": glue_job.ref},
                api_version="2017-03-31"
            )
        )

        glue_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["glue:StartJobRun"],
                resources=[f"arn:aws:glue:{self.region}:{self.account}:job/{glue_job.ref}"]
            )
        )

        # 9. IAM Role for DeepAR Dataset Glue Job
        etl_role = iam.Role(
            self, "GlueETLRoleForDeepAR",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
            ]
        )

        # 10. DeepAR Dataset Glue Job
        deepar_dataset_job = glue.CfnJob(
            self, "GenerateDeepARDatasetJob",
            name="GenerateDeepARDataset",
            role=etl_role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{data_bucket.bucket_name}/scripts/generate_deepar_dataset.py"
            ),
            glue_version="3.0",
            number_of_workers=2,
            worker_type="G.1X",
            max_retries=1
        )

        # 11. EventBridge Rule (3 AM UTC) to Trigger DeepAR Dataset Job
        deepar_schedule_rule = events.Rule(
            self, "DailyDeepARDatasetSchedule",
            schedule=events.Schedule.cron(minute="0", hour="3")
        )

        deepar_schedule_rule.add_target(
            targets.AwsApi(
                service="Glue",
                action="startJobRun",
                parameters={"JobName": deepar_dataset_job.ref},
                api_version="2017-03-31"
            )
        )

        etl_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["glue:StartJobRun"],
                resources=[f"arn:aws:glue:{self.region}:{self.account}:job/{deepar_dataset_job.ref}"]
            )
        )

        # 12. Output API URL
        self.api_url_output = CfnOutput(
            self, "InventoryAPIUrl",
            value=api.url
        )