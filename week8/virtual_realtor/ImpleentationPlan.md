Migration Roadmap: Index.html to SvelteKit
Context & Current State
Source: 
frontend/src/index.html
 is a standalone Vanilla JS/HTML page with a custom "Gold/Luxury" CSS theme and mock/vanilla-implemented auth UI.
Reference: frontend/admin is a modern SvelteKit app using TailwindCSS v4 and AWS Amplify v6.
Goal: Re-platform the "Chat" interface from 
index.html
 into a new SvelteKit application at frontend/app, inheriting the architecture of admin but preserving the "Gold/Luxury" aesthetics of the original 
index.html
 by porting them to Tailwind.
Auth: Must use existing Customer User Pool (Passwordless Email + OTP).
Phase 1: Project Initialization & Configuration
 Scaffold Project
Create new SvelteKit project in frontend/app (Skeleton project, TypeScript).
Command: npx sv create frontend/app (select Skeleton, TS).
 Dependency Parity
Install dependencies matching frontend/admin versions:
svelte@^5.0.0
tailwindcss@^4.0.0, @tailwindcss/vite
aws-amplify, @aws-amplify/auth
lucide-svelte
marked (for Markdown rendering in chat).
 Configuration replication
Copy 
vite.config.ts
 from admin (ensure Tailwind and SvelteKit plugins are present).
Copy 
tsconfig.json
 settings if necessary.
 Environment Setup
Create frontend/app/.env with:
PUBLIC_USER_POOL_ID=us-west-2_CA5WMVeTf
PUBLIC_USER_POOL_CLIENT_ID=6emisug81p9qlaonq4ufghsm2t
IMPORTANT

Checkpoint 1: Run npm run dev in frontend/app. Verify the default SvelteKit welcome page loads without errors.

Phase 2: Styling Infrastructure (Gold Theme)
 Tailwind Configuration
Configure Tailwind (v4 CSS or config file) to include the specific "Gold" palette from 
index.html
.
Colors to Port:
accent-primary: #f4b942
accent-secondary: #ffd978
bg-body-start: #ffffff -> #fef9f3 (Gradient)
 Global CSS
Create src/app.css importing Tailwind.
Add @theme directives or utility classes for the specific gradients used in body and chat-header.
 Font Setup
Import fonts (Inter/Roboto) in app.html or 
+layout.svelte
.
IMPORTANT

Checkpoint 2: Apply the "Gold" background gradient to 
+layout.svelte
. Verify the app background matches the original 
index.html
.

Phase 3: Core Architecture & components
 Authentication Logic
Create 
src/lib/auth.ts
.
Copy logic from ../admin/src/lib/auth.ts but update env var references to import.meta.env if the usage pattern differs in the new app structure, or keep standard Vite env access.
 Component Shells
Create component files in src/lib/components/:
Chat/ChatContainer.svelte
Chat/MessageBubble.svelte (Handles Markdown rendering)
Chat/InputArea.svelte
Auth/LoginModal.svelte
 Layout Implementation
Implement 
src/routes/+layout.svelte
:
Initialize Amplify.
Check Auth State (
checkIsAuthenticated
).
Manage global "User" state.
IMPORTANT

Checkpoint 3: Verify 
+layout.svelte
 mounts. Console logs should indicate whether a user is logged in (initially false).

Phase 4: Feature Implementation
 Login UI Port
Implement LoginModal.svelte.
Logic: Use 
startPasswordlessSignIn
 and 
completePasswordlessSignIn
 from 
auth.ts
.
Style: Recreate the Modal UI from 
index.html
 using Tailwind classes (e.g., fixed inset-0 bg-black/50 flex items-center justify-center).
 Chat Interface Port
Implement ChatContainer.svelte:
Render list of messages.
Handle "Thinking..." state.
Implement MessageBubble.svelte:
Use marked to render content.
Apply Gold/Pink styling based on role (Assistant/User).
 Chat Logic Integration
Port sendMessage() logic from 
index.html
.
Ensure it calls the backend API (you may need to configure 
vite.config.ts
 proxy to forward /api requests to the backend, or update the fetch URL).
IMPORTANT

Checkpoint 4:

Complete a Login flow (Email -> OTP).
Send a "Hello" message in the chat.
Verify the response is displayed correctly.
Phase 5: Cleanup & Polish
 Theme Toggling
Port Dark Mode logic (using Tailwind's dark: modifier).
 Final Review
Compare side-by-side with 
index.html
.
Ensure "Clear Session" and "Logout" work.
 Legacy Cleanup
Remove frontend/src (legacy static site).
Remove 
frontend/LOGIN_PLAN.md
, 
frontend/TODO.md
 and other temporary files.
