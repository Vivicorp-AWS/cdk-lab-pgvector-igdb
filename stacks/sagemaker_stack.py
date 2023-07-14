from aws_cdk import (
    NestedStack,
    aws_iam as iam,
    aws_sagemaker as sagemaker,
    CfnOutput,
    )
from constructs import Construct

# [TODO] Add a SageMaker Notebook Instance
# [TODO] Add a Serverless Inference Endpoint

class SageMakerNotebookStack(NestedStack):
    def __init__(self, scope: Construct, id: str, db_secret, parameter_dbsecretarn, security_group_ids, subnet_id:str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # SageMaker Execution Role
        sagemaker_role = iam.Role(self, "SageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            description="SageMaker Execution Role",
        )

        # Add "AmazonSageMakerFullAccess" and "SecretsManagerReadWrite" managed policies to SageMaker Execution Role
        sagemaker_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"))
        # Grant SageMaker Execution Role read/write access to Database Secret
        db_secret.grant_read(sagemaker_role)
        # Grant SageMaker Execution Role read access to Parameter Store secret
        parameter_dbsecretarn.grant_read(sagemaker_role)

        # SageMaker Notebook Instance
        notebook_instance = sagemaker.CfnNotebookInstance(self, "pgvectorDemoNotebook",
            instance_type="ml.t3.medium",
            role_arn=sagemaker_role.role_arn,
            default_code_repository="https://github.com/Vivicorp-AWS/cdk-lab-pgvector-igdb.git",
            direct_internet_access="Enabled",
            root_access="Enabled",
            security_group_ids=security_group_ids,
            subnet_id=subnet_id,
        )

        CfnOutput(self, "NotebookInstanceARN", value=notebook_instance.ref)  # Ref: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-sagemaker-notebookinstance.html#cfn-sagemaker-notebookinstance-notebookinstancename
        CfnOutput(self, "NotebookInstanceName", value=notebook_instance.get_att("NotebookInstanceName").to_string())
        