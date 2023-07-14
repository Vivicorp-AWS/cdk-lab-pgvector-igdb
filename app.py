#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.top_stack import TopStack
from stacks.vpc_stack import VPCStack
from stacks.rds_stack import RDSStack
from stacks.s3_stack import S3Stack
from stacks.lambda_stack import LambdaStack
from stacks.iam_stack import IAMStack
from stacks.sagemaker_stack import SageMakerNotebookStack
from constructs import DependencyGroup

app = cdk.App()

PREFIX = app.node.try_get_context("prefix")

top_stack = TopStack(
    app, f"{PREFIX}-pgvector-igdb-stack",
    description="CDK Lab pgvector IGDB Top Stack",
)

vpc_stack = VPCStack(
    top_stack, f"vpcs-tack",
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

sagemaker_stack = SageMakerNotebookStack(
    top_stack, f"sagemakerstack",
    description="CDK Lab pgvector IGDB SageMaker Stack",
    db_secret=db_secret,
    parameter_db_secret_arn=parameter_dbsecretarn,
    security_group_ids=[sg_allow_database_connection_id],
    subnet_id=public_subnet_id,
)

# Define dependencies
rds_stack.add_dependency(vpc_stack)
rds_and_s3_group = DependencyGroup()
rds_and_s3_group.add(rds_stack)
rds_and_s3_group.add(s3_stack)
lambda_stack.add_dependency(rds_and_s3_group)
sagemaker_stack.add_dependency(rds_and_s3_group)

app.synth()
