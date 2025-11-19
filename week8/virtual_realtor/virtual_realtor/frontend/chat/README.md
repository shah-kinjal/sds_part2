# Virtual Realtor Chat Frontend

This is a SvelteKit-based chat interface for the Virtual Realtor application with AWS Cognito authentication.

## Features

- 🔐 **AWS Cognito Authentication** - Username/password login
- 💬 **Real-time Chat** - Streaming responses from AI assistant
- 📝 **Markdown Support** - Rich text rendering for assistant responses
- 🔄 **Session Persistence** - Chat history saved across sessions
- 🎨 **Beautiful UI** - Gradient design with smooth animations

## Prerequisites

Before running the application, you need to configure AWS Cognito:

### AWS Cognito Setup

1. Create a Cognito User Pool named `vr-user-pool`
2. Configure the user pool for username/password authentication
3. Create an App Client (without client secret)
4. Note down:
   - User Pool ID (e.g., `us-west-2_xxxxxxxxx`)
   - User Pool Client ID (e.g., `xxxxxxxxxxxxxxxxxxxxxxxxxx`)

### Environment Variables

Create environment variables for the Cognito configuration. During build time, these should be available as:

- `PUBLIC_VITE_COGNITO_USER_POOL_ID`
- `PUBLIC_VITE_COGNITO_USER_POOL_CLIENT_ID`

For local development with Vite, create a `.env` file:

```bash
PUBLIC_VITE_COGNITO_USER_POOL_ID=us-west-2_xxxxxxxxx
PUBLIC_VITE_COGNITO_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Development

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Building

To create a production build:

```bash
npm run build
```

This will generate static files in the `build` directory that can be deployed.

## Preview Production Build

```bash
npm run preview
```

## Authentication Flow

1. User visits the app and is redirected to `/login`
2. User enters username and password
3. AWS Cognito validates credentials
4. Upon successful authentication, user is redirected to chat interface
5. Session is maintained via Amplify auth tokens
6. User can sign out from the top navigation bar

## Creating Test Users

To create users in the Cognito User Pool:

### Using AWS CLI:

```bash
aws cognito-idp admin-create-user \
  --user-pool-id us-west-2_xxxxxxxxx \
  --username testuser \
  --temporary-password TempPassword123! \
  --user-attributes Name=email,Value=test@example.com

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id us-west-2_xxxxxxxxx \
  --username testuser \
  --password YourPassword123! \
  --permanent
```

### Using AWS Console:

1. Go to Cognito User Pools
2. Select `vr-user-pool`
3. Click "Create user"
4. Enter username and set a permanent password

## Deployment

The app uses `@sveltejs/adapter-static` for static site generation. Deploy to:

- AWS S3 + CloudFront
- Vercel, Netlify, or similar platforms
- Through API Gateway + Lambda (same as backend)

Make sure to configure environment variables in your deployment platform.

