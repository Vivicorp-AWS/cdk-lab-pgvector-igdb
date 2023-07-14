#!/usr/bin/env python3

from aws_cdk import (
    NestedStack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
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
        prefix: str,
        security_groups=None,
        instance_type:ec2.InstanceType=ec2.InstanceType.of(
            ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),  # Default instance type: db.t4g.micro
        engine_version:rds.PostgresEngineVersion=rds.PostgresEngineVersion.VER_15_2,  # Default: PostgreSQL v15.2
        **kwargs) -> None:
        
        super().__init__(scope, id, **kwargs)

        # PostgreSQL for RDS Database Instance
        self.db = rds.DatabaseInstance(self, "PostgreSQL",
            engine=rds.DatabaseInstanceEngine.postgres(version=engine_version),
            instance_type=instance_type,
            backup_retention=Duration.days(0),
            auto_minor_version_upgrade=False,
            cloudwatch_logs_retention=logs.RetentionDays.ONE_MONTH,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_group_name="Private"),
            port=5432,
            security_groups=security_groups,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False
        )

        # Link a Secrets Manager secret to the RDS instance
        secretsmanager.SecretTargetAttachment(self, "MySecretTargetAttachment",
            secret=self.db.secret,
            target=self.db
        )

        self.parameter_dbsecretarn = ssm.StringParameter(self, "DBSecretARN", parameter_name=f"/{prefix}/DBSecretARN" ,string_value=self.db.secret.secret_arn)

        # Outputs
        CfnOutput(self, "DatabaseInstanceIdentifier", value=self.db.instance_identifier,)
        CfnOutput(self, "DatabaseInstanceARN", value=self.db.instance_arn,)
        CfnOutput(self, "DatabaseSecretName", value=self.db.secret.secret_name,)
        CfnOutput(self, "DatabaseSecretARN", value=self.db.secret.secret_arn,)
        CfnOutput(self, "SSMParameterDBSecretName", value=self.parameter_dbsecretarn.parameter_name,)
        CfnOutput(self, "SSMParameterDBSecretARN", value=self.parameter_dbsecretarn.parameter_arn,)
