#!/usr/bin/env python3
from dotenv import load_dotenv
import os
import sys
import aws_cdk as cdk
from stacks.top_stack import TopStack
from stacks.vpc_stack import VPCStack
from stacks.iam_stack import IAMStack
from stacks.rds_stack import RDSStack

app = cdk.App()

PREFIX = app.node.try_get_context("prefix")

top_stack = TopStack(
    app, f"{PREFIX}-pgvector-igdb-topstack",
    description="CDK Lab pgvector IGDB Top Stack",
)

vpc_stack = VPCStack(
    top_stack, f"vpcstack",
    description="CDK Lab pgvector IGDB VPC Stack",
)
sg_rds = vpc_stack.sg_rds

rds_stack = RDSStack(
    top_stack, f"rdsstack",
    description="CDK Lab pgvector IGDB RDS Stack",
    vpc=vpc_stack.vpc,
    security_groups=[sg_rds],
)
db_secret = rds_stack.db.secret
db_secret_arn = rds_stack.db.secret.secret_arn
db_identifier = rds_stack.db.instance_identifier

iam_stack = IAMStack(
    top_stack, f"iamstack",
    description="CDK Lab pgvector IGDB IAM Stack",
    db_identifier=db_identifier,
    db_secret_arn=db_secret_arn,
)

app.synth()
