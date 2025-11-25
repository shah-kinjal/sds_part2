import os
from aws_cdk.aws_dynamodb import TableV2
from aws_cdk import Duration, BundlingOptions, Fn, Stack
from constructs import Construct
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_sns as sns
from dotenv import load_dotenv


load_dotenv()  # Ensure local .env values are available when synthesizing


class Backend(Construct):
    endpoint: str
    domain_name: str

    def __init__(self, scope: Construct, id: str,
                 kb_arn: str, # Bedrock Knowledge Base ARN
                 kb_id: str,  # Bedrock Knowledge Base ID
                 dynamo_db_table: TableV2, # Used to store unanswered questions
                 openai_api_key: str | None = None, # OpenAI API key
                 openai_model_id: str = "gpt-4o", # OpenAI model ID
                 rentcast_api_key: str | None = None, # Rentcast API key
                 rental_cast_api_key: str | None = None, # Rental cast API key
                 rentcast_api_url: str | None = None, # Rentcast API URL
                 rental_cast_api_url: str | None = None, # Rental cast API URL
                 ) -> None:
        super().__init__(scope, id)

        # Pull optional OpenAI settings from env when not provided explicitly
        openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        openai_model_id = openai_model_id or os.environ.get("OPENAI_MODEL_ID") or "gpt-4o"
        # Accept either spelling and propagate both to the Lambda env
        rentcast_api_key = rentcast_api_key or os.environ.get("RENTCAST_API_KEY", "")
        rental_cast_api_key = rental_cast_api_key or os.environ.get("RENTAL_CAST_API_KEY", "")
        rentcast_api_url = rentcast_api_url or os.environ.get("RENTCAST_API_URL", "https://api.rentcast.io/v1/listings/sale")
        rental_cast_api_url = rental_cast_api_url or os.environ.get("RENTAL_CAST_API_URL", "https://api.rentcast.io/v1/listings/sale")

        state_bucket = s3.Bucket(self, 'StateBucket')
        notification_topic = sns.Topic(self, 'StateNotificationTopic')
        fn = _lambda.Function(self, 'StateFunction',
                              function_name='VirtualRealtor',
                              timeout=Duration.seconds(120),
                              architecture=_lambda.Architecture.X86_64,
                              runtime=_lambda.Runtime.PYTHON_3_13,
                              handler='run.sh',
                              code=_lambda.Code.from_asset('virtual_realtor/backend/src',
                                    bundling=BundlingOptions(
                                        image=_lambda.Runtime.PYTHON_3_13.bundling_image,
                                        command=[
                                            'bash', '-c',
                                            'pip install uv && uv export --frozen --no-dev --no-editable -o requirements.txt && pip install -r requirements.txt -t /asset-output && cp -r app/* /asset-output/'
                                        ],
                                        user='root',
                                        platform='linux/amd64',
                                    ),
                              ),
                              layers=[
                                    _lambda.LayerVersion.from_layer_version_arn(
                                        self,
                                        'LambdaAdapterLayer',
                                        f'arn:aws:lambda:{Stack.of(self).region}:753240598075:layer:LambdaAdapterLayerX86:25'
                                    )
                              ],
                              environment={
                                    "AWS_LAMBDA_EXEC_WRAPPER": "/opt/bootstrap",
                                    "AWS_LWA_INVOKE_MODE": "response_stream",
                                    "DDB_TABLE": dynamo_db_table.table_name,
                                    "KNOWLEDGE_BASE_ID": kb_id,
                                    "MODEL_ID": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
                                    "LLM_AS_A_JUDGE_MODEL_ID": "us.amazon.nova-pro-v1:0",
                                    "OPENAI_API_KEY": openai_api_key,
                                    "OPENAI_MODEL_ID": openai_model_id,
                                    "PORT": "8000",
                                    "STATE_BUCKET": state_bucket.bucket_name,
                                    "NOTIFICATION_TOPIC_ARN": notification_topic.topic_arn,
                                    "RENTCAST_API_KEY": rentcast_api_key,
                                    "RENTAL_CAST_API_KEY": rental_cast_api_key,
                                    "PROPERTY_TTL_HOURS": os.environ.get("PROPERTY_TTL_HOURS", "12"),
                                },
                              memory_size=1024,
                             )

        _ = state_bucket.grant_read_write(fn)
        _ = dynamo_db_table.grant_read_write_data(fn)
        _ = notification_topic.grant_publish(fn)
        # Add Bedrock permissions to the Lambda function
        fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:InvokeModel"
                ],
                resources=["*"]
            )
        )
        fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:RetrieveAndGenerate",
                    "bedrock:Retrieve",
                ],
                resources=[kb_arn]
            )
        )

        fn_url = fn.add_function_url(
                auth_type=_lambda.FunctionUrlAuthType.NONE,
                invoke_mode=_lambda.InvokeMode.RESPONSE_STREAM,
                cors=_lambda.FunctionUrlCorsOptions(
                    allowed_methods=[_lambda.HttpMethod.ALL],
                    allowed_origins=['*'],
                ),
            )
        self.endpoint = fn_url.url
        self.domain_name = Fn.select(2, Fn.split('/', self.endpoint)) # Remove the protocol part from the URL
