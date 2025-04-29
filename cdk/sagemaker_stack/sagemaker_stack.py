from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_sagemaker as sagemaker,
    CfnOutput,
)
from constructs import Construct

class SageMakerStudioStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.IVpc, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        subnet_ids = [subnet.subnet_id for subnet in vpc.private_subnets]
        vpc_id = vpc.vpc_id
        self.vpc = vpc

        # 1. SageMaker Execution Role
        sagemaker_role = iam.Role(
            self, "SageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
            ]
        )

        # 2. SageMaker Studio Domain (PublicInternetOnly)
        studio_domain = sagemaker.CfnDomain(
            self, "SageMakerStudioDomain",
            auth_mode="IAM",
            default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=sagemaker_role.role_arn
            ),
            domain_name="domain-04-25-2025-092423", 
            vpc_id="vpc-0496e679ca96b4968",   # <<< Provide EMPTY string
            subnet_ids=["subnet-0e82de44c4a76ee9a", "subnet-09d05abf5ce850f67"],  
            app_network_access_type="VpcOnly"
        )

        # 3. Create Default User Profile
        sagemaker.CfnUserProfile(
            self, "SageMakerUserProfile",
            domain_id=studio_domain.attr_domain_id,
            user_profile_name="default-user",
            user_settings=sagemaker.CfnUserProfile.UserSettingsProperty(
                execution_role=sagemaker_role.role_arn
            )
        )

        # 4. Output Studio Domain login link
        CfnOutput(
            self, "SageMakerStudioLoginUrl",
            value=f"https://dzd_bg0kt9c9y6u8vb.sagemaker.us-east-1.on.aws/",
            description="SageMaker Studio Login URL"
        )
