import aws_cdk as cdk
from aws_cdk.aws_s3 import Bucket
from virtual_realtor.backend.infra import Backend
from virtual_realtor.frontend.infra import Frontend
from virtual_realtor.admin.infra import Admin
from virtual_realtor.rum.infra import Rum
from virtual_realtor.customer_auth import CustomerAuth

class VirtualRealtor(cdk.Stack):
    def __init__(self, scope: cdk.App, id: str,
                 kb_arn: str, # Bedrock Knowledge Base ARN
                 kb_id: str,  # Bedrock Knowledge Base ID
                 kb_data_src_id: str, # Bedrock Knowledge Base Data Source ID
                 kb_input_bucket: Bucket,
                 openai_api_key: str | None = None,  # Optional OpenAI API key
                 openai_model_id: str = "gpt-4o",  # OpenAI model ID
                 custom_certificate_arn: str|None = None,  # Optional custom ACM certificate ARN
                 custom_certificate_name: str|None = None,  # Optional custom ACM certificate name
                 custom_domain_name: str|None = None,  # Optional custom domain name
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        admin = Admin(self, 'Admin',
                      kb_id=kb_id,  # Bedrock Knowledge Base ID
                      kb_data_src_id=kb_data_src_id,  # Bedrock Knowledge Base Data Source ID
                      kb_input_bucket=kb_input_bucket,  # S3 Bucket for input documents
                     )
        customer_auth = CustomerAuth(self, 'CustomerAuth')

        backend = Backend(self, 'Backend',
                          kb_arn=kb_arn,
                          kb_id=kb_id,
                          dynamo_db_table=admin.dynamodb_table,
                          openai_api_key=openai_api_key,
                          openai_model_id=openai_model_id,
                          user_pool_id=customer_auth.user_pool.user_pool_id,
                          user_pool_client_id=customer_auth.client.user_pool_client_id,
                         )
        
        frontend = Frontend(self, 'Frontend',
                            backend_endpoint=backend.domain_name,
                            admin_endpoint=admin.domain_name,
                            user_pool_id=admin.user_pool_id,
                            user_pool_client_id=admin.user_pool_client_id,
                            custom_certificate_arn=custom_certificate_arn,
                            custom_domain_name=custom_domain_name,
                           )

        _ = Rum(self, 'Rum',
                  domain_name=custom_domain_name or frontend.domain_name,
                 )

        _ = cdk.CfnOutput(
            self, 
            'FrontendURL',
            value=f"https://{frontend.domain_name}",
            description='Frontend UI URL'
        )
        if custom_domain_name:
            _ = cdk.CfnOutput(
                self,
                'CustomDomainURL',
                value=f"https://{custom_domain_name}",
                description='Custom domain URL'
            )

        _ = cdk.CfnOutput(
            self,
            'CustomerUserPoolId',
            value=customer_auth.user_pool.user_pool_id,
            description='Customer User Pool ID'
        )
        
        _ = cdk.CfnOutput(
            self,
            'CustomerUserPoolClientId',
            value=customer_auth.client.user_pool_client_id,
            description='Customer User Pool Client ID'
        )
