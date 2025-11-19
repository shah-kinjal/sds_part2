# Virtual Realtor Chat - Svelte Setup

This frontend has been converted from a single HTML file to a full SvelteKit application, following the same structure as the admin panel.

## Structure

```
chat/
├── src/
│   ├── routes/              # SvelteKit pages
│   │   ├── +layout.svelte   # Root layout
│   │   ├── +layout.ts       # Layout config
│   │   └── +page.svelte     # Main chat page
│   ├── lib/                 # Reusable components & utilities
│   │   ├── api.ts           # API functions
│   │   ├── types.ts         # TypeScript types
│   │   └── assets/          # Static assets
│   ├── app.css              # Global styles with Tailwind
│   ├── app.html             # HTML template
│   └── app.d.ts             # TypeScript declarations
├── static/                  # Static files served as-is
├── package.json             # Dependencies
├── svelte.config.js         # SvelteKit configuration
├── vite.config.ts           # Vite configuration
└── tsconfig.json            # TypeScript configuration
```

## Features

- ✅ Modern SvelteKit 2.0 with TypeScript
- ✅ **AWS Cognito Authentication** - Username/password login
- ✅ Tailwind CSS for styling
- ✅ Markdown rendering with marked.js
- ✅ Real-time streaming responses
- ✅ Chat history persistence
- ✅ Clear chat functionality
- ✅ Beautiful gradient UI matching original design
- ✅ Responsive and mobile-friendly
- ✅ Session management via cookies
- ✅ Protected routes with authentication guards

## Prerequisites

### AWS Cognito User Pool

You need to set up AWS Cognito authentication:

1. Create a Cognito User Pool named `vr-user-pool`
2. Configure it for username/password authentication
3. Create an App Client (without client secret)
4. Get your User Pool ID and Client ID

### Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Then edit `.env` with your Cognito details:

```bash
PUBLIC_VITE_COGNITO_USER_POOL_ID=us-west-2_xxxxxxxxx
PUBLIC_VITE_COGNITO_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Installation

```bash
cd /Users/kinjal/projects/sds_part2/week8/virtual_realtor/virtual_realtor/frontend/chat
npm install
```

## Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Building for Production

```bash
npm run build
```

This creates a static build in the `build/` directory.

## API Endpoints Used

- `GET /api/chat` - Load chat history
- `POST /api/chat` - Send a message (streaming response)
- `DELETE /api/chat` - Clear chat history

## Key Differences from Original

1. **AWS Cognito Authentication**: Secure login with username/password
2. **Protected Routes**: Authentication guards on all routes except login
3. **Modular Structure**: Code is now split into components and utilities
4. **TypeScript**: Full type safety throughout the app
5. **Tailwind CSS**: Using utility classes instead of inline styles
6. **SvelteKit**: Modern framework with routing, SSR capabilities, and more
7. **Better Developer Experience**: Hot module replacement, linting, formatting

## Deployment

The app is configured with `@sveltejs/adapter-static` for static site generation. The build output can be:

- Served via AWS S3 + CloudFront
- Deployed to any static hosting service
- Served through the same Lambda/API Gateway as the backend

## Configuration

To change the API base URL, edit `src/lib/api.ts`:

```typescript
const API_BASE = '/api'; // Change this if needed
```

