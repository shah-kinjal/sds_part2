#!/usr/bin/env python3
import os

import aws_cdk as cdk

from kb.stack import KnowledgeBase
from virtual_realtor.stack import VirtualRealtor

env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region='us-west-2')
app = cdk.App()
kb = KnowledgeBase(app, "RealtorKnowledgeBaseStack", env=env)
_ = VirtualRealtor(app, "VirtualRealtor",
         kb_arn=kb.kb.knowledge_base_arn,
         kb_id=kb.kb.knowledge_base_id,
         kb_data_src_id=kb.kb.data_source_id,
         kb_input_bucket=kb.input_bucket,
         openai_api_key=os.getenv('OPENAI_API_KEY'),  # Read from environment
         openai_model_id=os.getenv('OPENAI_MODEL_ID', 'gpt-4o'),  # Read from environment, default to gpt-4o
         custom_certificate_name="ShahKinjal.com cert's Virtual Realtor Certificate",
         custom_certificate_arn="arn:aws:acm:us-east-1:798627562337:certificate/d1f653e2-5caf-450b-8100-2c5abdde9a9a",
         custom_domain_name="vr.shahkinjal.com",
         env=env,
        )

app.synth()
