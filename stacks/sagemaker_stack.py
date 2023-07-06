from aws_cdk import (
    NestedStack,
    aws_sagemaker as sagemaker,
    CfnOutput,
    )
from constructs import Construct

# [TODO] Add a SageMaker Notebook Instance
# [TODO] Add a Serverless Inference Endpoint

class SageMakerStack(NestedStack):
    def __init__(self, scope: Construct, id: str, role_arn:str, security_group_ids, subnet_id:str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        notebook_instance = sagemaker.CfnNotebookInstance(self, "pgvectorDemoNotebook",
            instance_type="ml.t3.medium",
            role_arn=role_arn,
            default_code_repository="https://github.com/Vivicorp-AWS/cdk-lab-pgvector-igdb.git",
            direct_internet_access="Enabled",
            root_access="Enabled",
            security_group_ids=security_group_ids,
            subnet_id=subnet_id,
        )

        CfnOutput(self, "NotebookInstanceARN", value=notebook_instance.ref)  # Ref: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-sagemaker-notebookinstance.html#cfn-sagemaker-notebookinstance-notebookinstancename
        CfnOutput(self, "NotebookInstanceName", value=notebook_instance.get_att("NotebookInstanceName").to_string())
        