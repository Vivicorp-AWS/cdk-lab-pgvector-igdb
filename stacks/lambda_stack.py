from aws_cdk import (
    NestedStack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_ec2 as ec2,
    aws_logs as logs,
    Duration,
    triggers,
    CfnOutput,
)
from constructs import Construct
import os
import platform

class LambdaStack(NestedStack):

    def __init__(self, scope: Construct, id: str, db_secret, bucket, vpc, security_groups,**kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # [NOTE] pgvector-python has Numpy as dependency.
        # Refer to https://stackoverflow.com/a/76553058/2975670,
        # and visit Numpy's download page at PyPI (https://pypi.org/project/numpy/#files),
        # we found that the only platform that we can download is "manylinux_2_17_x86_64",
        # so download with "pip install --target ./layer/python --platform manylinux_2_17_x86_64 --only-binary=:all: --no-cache-dir -r requirements-layer.txt"
        layer = lambda_.LayerVersion(
            self, 'LambdaLayer',
            description='Python layer for send-task-lambda-function"',
            code=lambda_.Code.from_asset("layer"),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_9,
                lambda_.Runtime.PYTHON_3_10],
            removal_policy=RemovalPolicy.DESTROY
            )
        
        # architecture = lambda_.Architecture.ARM_64 if platform.machine() == 'arm64' else lambda_.Architecture.X86_64

        function = lambda_.Function(
            self, "DataImportLambdaFunction",
            code=lambda_.Code.from_asset(os.path.join(os.curdir, "lambda",)),
            architecture=lambda_.Architecture.X86_64,
            handler="index.handler",
            environment={
                "DB_SECRET_ARN": db_secret.secret_arn,
                "BUCKET_NAME": bucket.bucket_name,
                },
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=security_groups,
            runtime=lambda_.Runtime.PYTHON_3_10,
            layers=[layer],
            log_retention=logs.RetentionDays.ONE_DAY,
            timeout=Duration.seconds(60),
            )

        bucket.grant_read(function.role)
        db_secret.grant_read(function.role)
        
        triggers.Trigger(
            self, "DataImportLambdaFunctionTrigger",
            handler=function,
            invocation_type=triggers.InvocationType.EVENT,  # Async Trigger
            execute_on_handler_change=True,
            )

        CfnOutput(self, "LambdaFunctionName", value=function.function_name)
        CfnOutput(self, "LambdaFunctionArn", value=function.function_arn)
