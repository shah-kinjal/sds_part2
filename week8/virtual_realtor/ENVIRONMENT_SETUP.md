# Environment Setup Guide - Virtual Realtor

## Required Environment Variables

Before deploying the Virtual Realtor application, you need to set up the following environment variables:

### OpenAI Configuration

1. **OPENAI_API_KEY** (Required)
   - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
   - This key is used to authenticate with OpenAI's API
   
2. **OPENAI_MODEL_ID** (Optional, defaults to `gpt-4o`)
   - Specify which OpenAI model to use
   - Common options: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`

### AWS Configuration

These are automatically configured by AWS CDK:
- **CDK_DEFAULT_ACCOUNT**: Your AWS account ID
- **CDK_DEFAULT_REGION**: AWS region (currently set to `us-west-2`)

## Setup Instructions

### Option 1: Export in Terminal

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
export OPENAI_MODEL_ID="gpt-4o"  # Optional
```

### Option 2: Create a .env file

Create a `.env` file in the `week8/Virtual_Realtor` directory:

```bash
# .env file
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_ID=gpt-4o
```

Then source it before deployment:

```bash
source .env
```

### Option 3: Use direnv (Recommended)

If you have [direnv](https://direnv.net/) installed:

1. Create a `.envrc` file in the `week8/Virtual_Realtor` directory
2. Add the environment variables
3. Run `direnv allow`

## Deployment

After setting up the environment variables, deploy the stack:

```bash
cd week8/Virtual_Realtor
uv run cdk deploy
```

## Security Notes

- **Never commit your API keys** to version control
- The `.env` and `.envrc` files are already in `.gitignore`
- API keys are securely stored as Lambda environment variables in AWS
- Consider using AWS Secrets Manager for production deployments

## Verification

To verify your environment variables are set:

```bash
echo $OPENAI_API_KEY
echo $OPENAI_MODEL_ID
```

The OPENAI_API_KEY should show your key, and OPENAI_MODEL_ID should show the model name (or be empty, which defaults to gpt-4o).

