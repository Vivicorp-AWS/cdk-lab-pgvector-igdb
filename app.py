#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.top_stack import TopStack
from stacks.vpc_stack import VPCStack
from stacks.iam_stack import IAMStack
from stacks.rds_stack import RDSStack
from stacks.sagemaker_stack import SageMakerNotebookStack

app = cdk.App()

PREFIX = app.node.try_get_context("prefix")

top_stack = TopStack(
    app, f"{PREFIX}-pgvector-igdb-stack",
    description="CDK Lab pgvector IGDB Top Stack",
)

vpc_stack = VPCStack(
    top_stack, f"vpcstack",
    description="CDK Lab pgvector IGDB VPC Stack",
)
sg_rds = vpc_stack.sg_rds
sg_sagemaker_notebook_id = vpc_stack.sg_sagemaker_notebook.security_group_id
public_subnet_id = vpc_stack.vpc.public_subnets[0].subnet_id

rds_stack = RDSStack(
    top_stack, f"rdsstack",
    description="CDK Lab pgvector IGDB RDS Stack",
    vpc=vpc_stack.vpc,
    security_groups=[sg_rds],
    prefix=PREFIX,
)
db_secret = rds_stack.db.secret
db_secret_arn = rds_stack.db.secret.secret_arn
db_identifier = rds_stack.db.instance_identifier
parameter_db_secret_arn = rds_stack.parameter_db_secret_arn

# [NOTE] Combine IAMStack into SageMakerStack?
iam_stack = IAMStack(
    top_stack, f"iamstack",
    description="CDK Lab pgvector IGDB IAM Stack",
    db_identifier=db_identifier,
    db_secret_arn=db_secret_arn,
    parameter_db_secret_arn=parameter_db_secret_arn,
)
sagemaker_role_arn = iam_stack.sagemaker_role.role_arn

sagemaker_stack = SageMakerNotebookStack(
    top_stack, f"sagemakerstack",
    description="CDK Lab pgvector IGDB SageMaker Stack",
    role_arn=sagemaker_role_arn,
    security_group_ids=[sg_sagemaker_notebook_id],
    subnet_id=public_subnet_id,
)

app.synth()
