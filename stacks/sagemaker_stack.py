from aws_cdk import (
    NestedStack,
    aws_iam as iam,
    aws_sagemaker as sagemaker,
    CfnOutput,
    CfnTag,
    )
from constructs import Construct

class SageMakerRoleStack(NestedStack):
    def __init__(self, scope: Construct, id: str, db_secret, bucket, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # SageMaker Execution Role
        self.sagemaker_role = iam.Role(self, "SageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            description="SageMaker Execution Role",
        )

        # Add "AmazonSageMakerFullAccess" and "SecretsManagerReadWrite" managed policies to SageMaker Execution Role
        self.sagemaker_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"))
        # Grant SageMaker Execution Role read/write access to Database Secret
        db_secret.grant_read(self.sagemaker_role)
        # Grant SageMaker Execution Role read access to S3 Bucket
        bucket.grant_read(self.sagemaker_role)

        CfnOutput(self, "SageMakerRoleARN", value=self.sagemaker_role.role_arn)

class SageMakerModelStack(NestedStack):

    def __init__(self, scope: Construct, id: str, sagemaker_role_arn:str, image:str, model_object_key:str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        model = sagemaker.CfnModel(
            self, "HuggingFaceInferenceModel",
                execution_role_arn=sagemaker_role_arn,
                containers=[
                    sagemaker.CfnModel.ContainerDefinitionProperty(
                        image=image,
                        model_data_url=model_object_key,
                    )
                ],
            )
        model_name = model.attr_model_name

        # [NOTE] When setting config, it is recommended to read the SageMaker Python package's reference and apply the default values
        production_variant_property = sagemaker.CfnEndpointConfig.ProductionVariantProperty(
            model_name=model_name,
            variant_name="all-MiniLM-L6-v2",
            initial_variant_weight=1.0,
            # Ref: https://sagemaker.readthedocs.io/en/stable/api/inference/serverless.html
            serverless_config=sagemaker.CfnEndpointConfig.ServerlessConfigProperty(  
                max_concurrency=5,
                memory_size_in_mb=2048,
                ),
            )
        endpoint_config = sagemaker.CfnEndpointConfig(
            self, "HuggingFaceInferenceModelEndpointConfig",
            production_variants=[
                production_variant_property,
                ],
        )
        endpoint_config_name = endpoint_config.attr_endpoint_config_name        
        self.endpoint = sagemaker.CfnEndpoint(
            self, "HuggingFaceInferenceModelEndpoint",
            endpoint_config_name=endpoint_config_name,
            )

        CfnOutput(self, "EndpointName", value=self.endpoint.attr_endpoint_name)

class SageMakerNotebookStack(NestedStack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            sagemaker_role_arn:str,
            security_group_ids,
            subnet_id:str,
            bucket_name:str,
            db_secret_arn:str,
            endpoint_name:str,
            **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # SageMaker Notebook Instance
        notebook_instance = sagemaker.CfnNotebookInstance(self, "pgvectorNotebook",
            instance_type="ml.t3.medium",
            role_arn=sagemaker_role_arn,
            default_code_repository="https://github.com/Vivicorp-AWS/cdk-lab-pgvector-igdb.git",
            direct_internet_access="Enabled",
            root_access="Enabled",
            security_group_ids=security_group_ids,
            subnet_id=subnet_id,
            tags=[  # Use tags to inject some necessary variables
                CfnTag(key="VAR_ASSETS_BUCKET", value=bucket_name),
                CfnTag(key="VAR_DB_SECRET_ARN", value=db_secret_arn),
                CfnTag(key="VAR_MODEL_ENDPOINT", value=endpoint_name),
            ],
        )

        CfnOutput(self, "NotebookInstanceARN", value=notebook_instance.ref)  # Ref: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-sagemaker-notebookinstance.html#cfn-sagemaker-notebookinstance-notebookinstancename
        CfnOutput(self, "NotebookInstanceName", value=notebook_instance.get_att("NotebookInstanceName").to_string())
