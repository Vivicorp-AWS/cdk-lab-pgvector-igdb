#!/usr/bin/env python3

from aws_cdk import (
    NestedStack,
    aws_ec2 as ec2,
    aws_rds as rds,
    SecretValue,
    aws_secretsmanager as secretsmanager,
    Duration,
    aws_logs as logs,
    RemovalPolicy,
    CfnOutput,
)

from constructs import Construct

class RDSStack(NestedStack):
    def __init__(
        self, scope:Construct,
        id:str,
        vpc,
        db_params=None,
        db_name:str="postgres",  # Default Database name: "postgres". Can't use PostgreSQL's reserved name "db" as database name
        db_secret=None,
        security_groups=None,
        instance_type:ec2.InstanceType=ec2.InstanceType.of(
            ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),  # Default instance type: db.t4g.micro
        engine_version:rds.PostgresEngineVersion=rds.PostgresEngineVersion.VER_15_2,  # Default: PostgreSQL v15.2
        **kwargs) -> None:
        
        super().__init__(scope, id, **kwargs)

        # PostgreSQL for RDS Database Instance
        self.db = rds.DatabaseInstance(self, "PostgreSQL",
            database_name=db_name,
            instance_identifier=db_params["identifier"],
            engine=rds.DatabaseInstanceEngine.postgres(version=engine_version),
            instance_type=instance_type,
            backup_retention=Duration.days(0),
            cloudwatch_logs_retention=logs.RetentionDays.ONE_MONTH,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="Private"),
            port=5432,
            security_groups=security_groups,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False
        )

        secretsmanager.SecretTargetAttachment(self, "MySecretTargetAttachment",
            secret=self.db.secret,
            target=self.db
        )

        # Outputs
        CfnOutput(self, "DatabaseInstanceIdentifier", value=self.db.instance_identifier,)
        CfnOutput(self, "DatabaseInstanceARN", value=self.db.instance_arn,)
        CfnOutput(self, "DatabaseSecretName", value=self.db.secret.secret_name,)
        CfnOutput(self, "DatabaseSecretARN", value=self.db.secret.secret_arn,)
