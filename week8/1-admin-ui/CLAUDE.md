# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AWS CDK-based application that deploys a digital twin chatbot with an admin interface. The application consists of:

1. **Knowledge Base Stack** (`kb/`): Bedrock Knowledge Base with S3 vector store for RAG
2. **Twin Stack** (`twin/`): The main application with three components:
   - **Backend**: FastAPI agent using Strands framework with Bedrock models and RAG
   - **Frontend**: Static HTML chat interface for end users
   - **Admin**: SvelteKit application for managing questions, visitors, and documents

## Architecture

The application uses a multi-stack CDK architecture:

- `app.py`: Root CDK app that orchestrates two stacks:
  - `KnowledgeBaseStack`: Creates S3-backed Bedrock Knowledge Base
  - `Twin`: Main application stack that:
    - Provisions Admin infrastructure (Cognito, DynamoDB, Lambda)
    - Provisions Backend Lambda (FastAPI with Strands agent)
    - Provisions Frontend (CloudFront + S3) with routing to admin and backend
    - Provisions RUM monitoring

### Backend Agent Architecture

The backend (`twin/backend/src/app/main.py`) implements an agentic chatbot using:

- **Strands Agent Framework**: Manages conversation state and tool execution
- **Bedrock Claude Sonnet 4.5**: Primary LLM (`global.anthropic.claude-sonnet-4-5-20250929-v1:0`)
- **RAG Enhancement** (`rag_enhancements.py`): Query rewriting and reranking capabilities
- **S3 Session Manager**: Persists conversation history in S3
- **DynamoDB**: Stores unanswered questions and visitor information

### Frontend Routing

CloudFront distribution routes requests:
- `/` → Frontend S3 bucket (static HTML chat interface)
- `/admin/*` → Admin frontend S3 bucket (SvelteKit SPA)
- `/api/*` → Backend Lambda (FastAPI endpoints)
- `/adminapi/*` → Admin Lambda (management APIs)
- `/_app/env.js` → Dynamic Cognito configuration for admin app

## Development Commands

### Deployment

```bash
# Deploy both stacks to AWS
uv run cdk deploy

# Deploy specific stack
uv run cdk deploy TwinKnowledgeBaseStack
uv run cdk deploy Twin
```

### CDK Operations

```bash
# Synthesize CloudFormation template
uv run cdk synth

# Show diff between deployed and local
uv run cdk diff

# Destroy deployed stacks
uv run cdk destroy
```

### Local Development

#### Backend
```bash
cd twin/backend/src
# Install dependencies
uv pip install -r requirements.txt
# Run locally (requires AWS credentials and env vars)
python -m app.main
```

#### Admin Frontend
```bash
cd twin/frontend/admin
npm ci
npm run dev
```

### Testing

```bash
# Run tests (if available)
uv run pytest tests/

# Test AWS credentials
aws sts get-caller-identity
```

## Environment Variables

Required environment variables (see `ENVIRONMENT_SETUP.md`):

- `OPENAI_API_KEY`: OpenAI API key (optional, used if configured)
- `OPENAI_MODEL_ID`: OpenAI model (default: `gpt-4o`)
- `CDK_DEFAULT_ACCOUNT`: AWS account ID (auto-configured by CDK)
- `CDK_DEFAULT_REGION`: AWS region (defaults to `us-west-2`)

Environment variables can be set via:
1. `export` in terminal
2. `.env` file (gitignored)
3. direnv with `.envrc` file

## Key Files and Components

### CDK Infrastructure

- `app.py`: Root CDK application entry point
- `kb/stack.py`: Bedrock Knowledge Base infrastructure
- `kb/vectorstore.py`: S3 vector store configuration
- `kb/bedrockkb.py`: Bedrock KB setup
- `twin/stack.py`: Main Twin stack orchestration
- `twin/backend/infra.py`: Backend Lambda and S3 state bucket
- `twin/frontend/infra.py`: CloudFront distribution and S3 buckets
- `twin/admin/infra.py`: Admin Lambda, Cognito, DynamoDB
- `twin/admin/cognito.py`: Cognito user pool configuration
- `twin/admin/apifn.py`: Admin API Lambda function

### Backend Application

- `twin/backend/src/app/main.py`: FastAPI application with agent logic
- `twin/backend/src/app/rag_enhancements.py`: RAG query rewriting and reranking
- `twin/backend/src/app/questions.py`: Question and visitor management models

The backend agent has three tools:
- `rag_retrieve`: Search knowledge base with enhanced RAG
- `save_unanswered_question`: Log questions that couldn't be answered
- `capture_visitor_info`: Record visitor name and email

### Admin Application

- `twin/admin/src/app/main.py`: Admin Lambda (FastAPI) for management APIs
- `twin/admin/src/app/auth.py`: JWT authentication utilities
- `twin/admin/src/app/questions.py`: DynamoDB operations for questions/visitors
- `twin/frontend/admin/`: SvelteKit frontend application

### Frontend

- `twin/frontend/src/index.html`: Static HTML chat interface
- `twin/frontend/admin/`: SvelteKit admin UI (built during deployment)

## Important Notes

### Lambda Deployment

Both backend and admin Lambdas use:
- Python 3.13 runtime
- `uv` for dependency management
- Bundling happens during `cdk deploy` via Docker
- Backend uses Lambda Web Adapter for FastAPI with response streaming
- Admin uses standard Lambda function URL

### Custom Domain

The application supports custom domains via ACM certificate:
- Certificate must be in `us-east-1` (for CloudFront)
- Configure via `custom_certificate_arn`, `custom_certificate_name`, and `custom_domain_name` in `app.py`
- Current domain: `twin.shahkinjal.com`

### DynamoDB Schema

The admin DynamoDB table uses single-table design:
- Partition Key: `PK`
- Sort Key: `SK`
- Stores questions with `PK=QUESTION`, `SK=<question_id>`
- Stores visitors with `PK=VISITOR`, `SK=<visitor_id>`

### Session Management

- Backend uses S3 for session persistence (stored in STATE_BUCKET)
- Session IDs stored in cookies
- Sessions contain conversation history managed by Strands `SlidingWindowConversationManager`

## Region Configuration

Default region is `us-west-2`. To change, update `app.py`:
```python
env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region='YOUR_REGION')
```

Note: Custom certificate must still be in `us-east-1` for CloudFront.
