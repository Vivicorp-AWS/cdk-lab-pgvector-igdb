from aws_cdk import Stack
from constructs import Construct

class TopStack(Stack):
    def __init__(
            self,
            scope: Construct,
            id: str,
            **kwargs,) -> None:
        super().__init__(scope, id, **kwargs)
