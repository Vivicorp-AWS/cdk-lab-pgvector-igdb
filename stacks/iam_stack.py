from aws_cdk import (
    NestedStack,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    aws_rds as rds,
    SecretValue,
    RemovalPolicy,
    CfnOutput,
)
import json
from constructs import Construct

class IAMStack(NestedStack):
    def __init__(self, scope: Construct, id: str, db_params, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.sagemaker_role = iam.Role(self, "SageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            description="SageMaker Execution Role",
        )
        self.sagemaker_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"))
        self.sagemaker_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"))

        self.db_secret = secretsmanager.Secret(self, "DatabaseSecret",
                                               secret_object_value={
                                                   "username": SecretValue.unsafe_plain_text(db_params["username"]),
                                                   "password": SecretValue.unsafe_plain_text(db_params["password"]),
                                               }
        )

        # self.db_secret = rds.DatabaseSecret(self, "DatabaseSecret",
        #                                     username="postgres"
        #                                     )

        self.sagemaker_role.attach_inline_policy(iam.Policy(self, "ReadDBSecretPolicy",
                                                          statements=[
            iam.PolicyStatement(
            actions=[
                "secretsmanager:GetResourcePolicy",
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret",
                "secretsmanager:ListSecretVersionIds",],
            resources=[self.db_secret.secret_arn]
            ),
            iam.PolicyStatement(
            actions=[
                "secretsmanager:GetRandomPassword",  # [TODO] Is this necessary?
                "secretsmanager:ListSecrets",],
            resources=["*"]
            )]
        ))

        self.sagemaker_role.attach_inline_policy(iam.Policy(self, "DescribeDBInstancesPolicy",
                                                          statements=[
            iam.PolicyStatement(
            actions=[
                "rds:DescribeDBInstances",
            ],
            resources=[f"arn:aws:rds:*:546614691476:db:{db_params['identifier']}"],
            )],
        ))

        self.sagemaker_role.apply_removal_policy(RemovalPolicy.DESTROY)

        CfnOutput(self, "DatabaseSecretName", value=self.db_secret.secret_name,)
        CfnOutput(self, "DatabaseSecretARN", value=self.db_secret.secret_arn,)
        CfnOutput(self, "SageMakerRoleName", value=self.sagemaker_role.role_name,)
        CfnOutput(self, "SageMakerRoleARN", value=self.sagemaker_role.role_arn,)
