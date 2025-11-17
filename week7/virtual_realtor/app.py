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
         env=env,
        )

app.synth()
