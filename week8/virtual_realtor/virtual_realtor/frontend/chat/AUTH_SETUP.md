# Authentication Setup Guide

This guide walks you through setting up AWS Cognito authentication for the Virtual Realtor chat frontend.

## Step 1: Create Cognito User Pool

### Using AWS CLI:

```bash
# Create the user pool
aws cognito-idp create-user-pool \
  --pool-name vr-user-pool \
  --policies "PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=false}" \
  --auto-verified-attributes email \
  --username-attributes email \
  --username-configuration CaseSensitive=false

# Note the UserPoolId from the output
```

### Using AWS Console:

1. Go to AWS Cognito in the AWS Console
2. Click "Create user pool"
3. Choose "Username" sign-in option and select "Also allow sign in with verified email"
4. Set password policy requirements
5. Name the pool `vr-user-pool`
6. Complete the wizard

## Step 2: Create App Client

### Using AWS CLI:

```bash
# Replace <user-pool-id> with your User Pool ID
aws cognito-idp create-user-pool-client \
  --user-pool-id <user-pool-id> \
  --client-name vr-chat-client \
  --no-generate-secret \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --read-attributes email \
  --write-attributes email

# Note the ClientId from the output
```

### Using AWS Console:

1. Select your user pool `vr-user-pool`
2. Go to "App clients" tab
3. Click "Create app client"
4. Name it `vr-chat-client`
5. **Important**: Uncheck "Generate client secret" (public web apps don't use secrets)
6. Under "Authentication flows" enable:
   - ALLOW_USER_PASSWORD_AUTH
   - ALLOW_REFRESH_TOKEN_AUTH
7. Create the app client

## Step 3: Configure Environment Variables

Create a `.env` file in the chat frontend directory:

```bash
PUBLIC_VITE_COGNITO_USER_POOL_ID=us-west-2_xxxxxxxxx
PUBLIC_VITE_COGNITO_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

Replace the values with your actual User Pool ID and Client ID.

## Step 4: Create Test Users

### Using AWS CLI:

```bash
# Create user with temporary password
aws cognito-idp admin-create-user \
  --user-pool-id <user-pool-id> \
  --username testuser \
  --temporary-password TempPassword123! \
  --user-attributes Name=email,Value=test@example.com

# Set permanent password (skip force change)
aws cognito-idp admin-set-user-password \
  --user-pool-id <user-pool-id> \
  --username testuser \
  --password MyPassword123! \
  --permanent
```

### Using AWS Console:

1. Go to your user pool
2. Click "Users" tab
3. Click "Create user"
4. Enter username (e.g., `testuser`)
5. Choose "Set a password"
6. Uncheck "Send an email invitation to this new user"
7. Enter a password meeting your policy requirements
8. Uncheck "Mark email address as verified" if not using email verification
9. Create the user

## Step 5: Test Authentication

1. Start the development server:
   ```bash
   npm run dev
   ```

2. Navigate to `http://localhost:5173`

3. You should be redirected to `/login`

4. Enter your test credentials

5. Upon successful login, you'll be redirected to the chat interface

## Troubleshooting

### "User does not exist" error
- Verify the username is correct
- Check that the user is in the correct user pool

### "Incorrect username or password" error
- Verify the password meets policy requirements
- If using a temporary password, set it to permanent

### "Invalid grant" error
- Ensure `ALLOW_USER_PASSWORD_AUTH` is enabled in the app client
- Check that the app client is associated with the correct user pool

### Environment variables not loading
- Make sure `.env` file is in the root of the chat directory
- Restart the dev server after creating/modifying `.env`
- Ensure variable names start with `PUBLIC_VITE_`

## Security Best Practices

1. **Never commit `.env` files** - They're in `.gitignore` by default
2. **Use environment-specific configs** - Different pools for dev/staging/prod
3. **Rotate credentials regularly** - Update app client IDs periodically
4. **Enable MFA** - For production, enable multi-factor authentication
5. **Monitor sign-in attempts** - Use CloudWatch to track failed login attempts
6. **Set up account recovery** - Configure email/SMS for password reset

## Production Deployment

For production deployments, set environment variables in your deployment platform:

### AWS Amplify:
Add environment variables in the Amplify Console under App Settings > Environment variables

### Vercel/Netlify:
Add environment variables in project settings

### CloudFormation/CDK:
Pass variables during stack deployment

Example CloudFormation parameter:
```yaml
Parameters:
  CognitoUserPoolId:
    Type: String
    Description: Cognito User Pool ID
  CognitoClientId:
    Type: String
    Description: Cognito App Client ID
```

## Additional Resources

- [AWS Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [AWS Amplify Auth Documentation](https://docs.amplify.aws/lib/auth/getting-started/q/platform/js/)
- [SvelteKit Environment Variables](https://kit.svelte.dev/docs/modules#$env-static-public)

