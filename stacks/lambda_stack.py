from aws_cdk import (
    Stack,
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

class LambdaStack(Stack):

    def __init__(self, scope: Construct, id: str, db_secret, bucket, vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        layer = lambda_.LayerVersion(
            self, 'LambdaLayer',
            description='Python layer for send-task-lambda-function"',
            code=lambda_.Code.from_asset("layer"),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_9,
                lambda_.Runtime.PYTHON_3_10],
            removal_policy=RemovalPolicy.DESTROY
            )

        funciton = lambda_.Function(
            self, "DataImportLambdaFunction",
            code=lambda_.Code.from_asset(os.path.join(os.curdir, "lambda",)),
            architecture=lambda_.Architecture.X86_64,
            handler="index.handler",
            environment={
                "DB_SECRET_ARN": db_secret.secret_arn,
                "BUCKET_NAME": bucket.bucket_name,
                },
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
            runtime=lambda_.Runtime.PYTHON_3_10,
            layers=[layer],
            log_retention=logs.RetentionDays.ONE_DAY,
            timeout=Duration.seconds(30),
            )
        bucket.grant_read(funciton.role)
        db_secret.grant_read(funciton.role)
        
        triggers.Trigger(
            self, "DataImportLambdaFunctionTrigger",
            handler=funciton,
            invocation_type=triggers.InvocationType.EVENT,  # Async Trigger
            execute_on_handler_change=True,
            )
        
        CfnOutput(self, "LambdaFunctionName", function.function_name)
        CfnOutput(self, "LambdaFunctionArn", function.function_arn)
