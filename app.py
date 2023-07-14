#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.top_stack import TopStack
from stacks.vpc_stack import VPCStack
from stacks.rds_stack import RDSStack
from stacks.s3_stack import S3Stack
from stacks.lambda_stack import LambdaStack
# from stacks.iam_stack import IAMStack
from stacks.sagemaker_stack import (
    SageMakerRoleStack,
    SageMakerNotebookStack,
    SageMakerModelStack,
    )
import sagemaker

app = cdk.App()

ACCOUNT = app.node.try_get_context("account")
REGION = app.node.try_get_context("region")
PREFIX = app.node.try_get_context("prefix")

IMAGE = sagemaker.image_uris.retrieve(
            framework='huggingface',
            region=REGION,
            version='4.26.0',
            image_scope='inference',
            base_framework_version='pytorch1.13.1',
            instance_type='ml.c6i.2xlarge',  # [NOTE] The function will return different image depends the usage of instance type focuses on CPU or GPU.
                                             # So for example, if you want to use GPU, you should fill in a instance type that is supported by GPU such as "ml.p3.8xlarge"
            )

top_stack = TopStack(
    app, f"{PREFIX}-pgvector-igdb-stack",
    description="CDK Lab pgvector IGDB Top Stack",
)

# [TODO] Use Stack instead of using NestedStack
vpc_stack = VPCStack(
    top_stack, f"vpc-stack",
    description="CDK Lab pgvector IGDB VPC Stack",
)
vpc = vpc_stack.vpc
sg_rds = vpc_stack.sg_rds
sg_allow_database_connection = vpc_stack.sg_allow_database_connection
sg_allow_database_connection_id = sg_allow_database_connection.security_group_id
public_subnets = vpc_stack.vpc.public_subnets
public_subnet_id = public_subnets[0].subnet_id

rds_stack = RDSStack(
    top_stack, f"rds-stack",
    description="CDK Lab pgvector IGDB RDS Stack",
    vpc=vpc_stack.vpc,
    security_groups=[sg_rds],
    prefix=PREFIX,
)
db_secret = rds_stack.db.secret
db_secret_arn = db_secret.secret_arn
db_identifier = rds_stack.db.instance_identifier
parameter_dbsecretarn = rds_stack.parameter_dbsecretarn

s3_stack = S3Stack(
    top_stack, f"s3-stack",
    description="CDK Lab pgvector IGDB S3 Stack",
)
bucket = s3_stack.bucket
bucket_name = bucket.bucket_name
model_object_key = f"s3://{bucket_name}/model.tar.gz"

lambda_stack = LambdaStack(
    top_stack, f"lambda-stack",
    description="CDK Lab pgvector IGDB Lambda Stack",
    db_secret=db_secret,
    bucket=bucket,
    vpc=vpc,
)

# # [NOTE] Combine IAMStack into SageMakerStack?
# iam_stack = IAMStack(
#     top_stack, f"iamstack",
#     description="CDK Lab pgvector IGDB IAM Stack",
#     db_identifier=db_identifier,
#     db_secret_arn=db_secret_arn,
#     parameter_db_secret_arn=parameter_db_secret_arn,
# )
# sagemaker_role_arn = iam_stack.sagemaker_role.role_arn

sagemaker_role_stack = SageMakerRoleStack(
    top_stack, f"sagemaker-role-stack",
    description="CDK Lab pgvector IGDB SageMaker Role Stack",
    db_secret=db_secret,
    parameter_dbsecretarn=parameter_dbsecretarn,
    bucket=bucket,
)
sagemaker_role = sagemaker_role_stack.sagemaker_role
sagemaker_role_arn = sagemaker_role.role_arn

sagemaker_model_stack = SageMakerModelStack(
    top_stack, f"sagemaker-model-stack",
    description="CDK Lab pgvector IGDB SageMaker Model Stack",
    sagemaker_role_arn=sagemaker_role_arn,
    image=IMAGE,
    model_object_key=model_object_key,
)

sagemaker_notebook_stack = SageMakerNotebookStack(
    top_stack, f"sagemaker-notebook-stack",
    description="CDK Lab pgvector IGDB SageMaker Notebook Stack",
    sagemaker_role_arn=sagemaker_role_arn,
    security_group_ids=[sg_allow_database_connection_id],
    subnet_id=public_subnet_id,
)

# Define dependencies
rds_stack.add_dependency(vpc_stack)
lambda_stack.add_dependency(rds_stack)
lambda_stack.add_dependency(s3_stack)
sagemaker_role_stack.add_dependency(rds_stack)
sagemaker_role_stack.add_dependency(s3_stack)
sagemaker_model_stack.add_dependency(sagemaker_role_stack)
sagemaker_notebook_stack.add_dependency(sagemaker_model_stack)

app.synth()
