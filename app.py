#!/usr/bin/env python3
from dotenv import load_dotenv
import os
import sys
import aws_cdk as cdk
from stacks.top_stack import TopStack
from stacks.vpc_stack import VPCStack
from stacks.iam_stack import IAMStack
from stacks.rds_stack import RDSStack

load_dotenv()

# Set the default database name
if os.getenv("DB_IDENTIFIER"):
    DB_IDENTIFIER = os.getenv("DB_IDENTIFIER")
else:
    print("Please specify DB_IDENTIFIER in .env file")
    sys.exit(1)

# Set the default database username
if os.getenv("DB_USERNAME"):
    DB_USERNAME = os.getenv("DB_USERNAME")
else:
    print("Please specify DB_USERNAME in .env file")
    sys.exit(1)

# Set the default database password
if os.getenv("DB_PASSWORD"):
    DB_PASSWORD = os.getenv("DB_PASSWORD")
else:
    print("Please specify DB_PASSWORD in .env file")
    sys.exit(1)

# Aggregrate database related parameters
db_params = {
    "username": DB_USERNAME,
    "password": DB_PASSWORD,
    "identifier": DB_IDENTIFIER,
}

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
    db_params=db_params,
    security_groups=[sg_rds],
)
db_secret = rds_stack.db.secret

iam_stack = IAMStack(
    top_stack, f"iamstack",
    description="CDK Lab pgvector IGDB IAM Stack",
    db_params=db_params,
    db_secret=db_secret,
)




app.synth()
