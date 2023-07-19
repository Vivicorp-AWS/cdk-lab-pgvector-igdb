from aws_cdk import (
    NestedStack,
    CfnOutput,
    )
import aws_cdk.aws_ec2 as ec2
from constructs import Construct

class VPCStack(NestedStack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # VPC in 2 azs, including 1 public and 1 private subnet in each az
        self.vpc = ec2.Vpc(
            self, "VPC",
            max_azs=2,
            ip_addresses=ec2.IpAddresses.cidr("10.10.0.0/16"),
            # configuration will create 2 groups in 2 AZs = 4 subnets.
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24
                    ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    name="Private",
                    cidr_mask=24
                    )
                ],
            )
        
        # Security group for computing workloads like SageMaker Notebook and Lambda Funciton
        self.sg_compute_workload = ec2.SecurityGroup(
            self, "AllowDatabaseConnectionSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=True,
        )

        # Security group for RDS for PostgreSQL instance
        self.sg_rds = ec2.SecurityGroup(
            self, "RDSSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=True,
        )
        self.sg_rds.add_ingress_rule(self.sg_compute_workload, ec2.Port.tcp(5432))

        # Security group for VPC Endpoints
        self.sg_vpce = ec2.SecurityGroup(
            self, "VPCESecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=True,
        )
        self.sg_vpce.add_ingress_rule(self.sg_compute_workload, ec2.Port.all_tcp())

        # Interface VPC Endpoint for Lambda Function to access SecretsManager
        self.vpc.add_interface_endpoint(
            "SecretsManagerInterfaceVPCEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[self.sg_vpce],
        )

        # Gateway VPC Endpoint for Lambda Function to access S3
        self.vpc.add_gateway_endpoint(
            "S3GatewayVPCEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)],
        )

        CfnOutput(self, "VPCARN", value=self.vpc.vpc_arn)