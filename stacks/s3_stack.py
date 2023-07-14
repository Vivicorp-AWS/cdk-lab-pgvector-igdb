from aws_cdk import (
    Stack,
    aws_s3 as s3,
    RemovalPolicy,
    aws_s3_deployment as s3deploy,
    Size,
    aws_s3_deployment as s3deploy,
    CfnOutput,
)
from constructs import Construct

class S3Stack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.bucket = s3.Bucket(
            self, "AssetsBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,)

        # Upload assets to bucket
        s3deploy.BucketDeployment(
            self, f"AssetsDeployment",
            sources=[s3deploy.Source.asset("./assets")],
            destination_bucket=self.bucket,
            memory_limit=256,
            ephemeral_storage_size=Size.mebibytes(1024),
            retain_on_delete=True,
            prune=False,
            )

        CfnOutput(self, "BucketName", value=self.bucket.bucket_name)
        CfnOutput(self, "BucketARN", value=self.bucket.bucket_arn)
