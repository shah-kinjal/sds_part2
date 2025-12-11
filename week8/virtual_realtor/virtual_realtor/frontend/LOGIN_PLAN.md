# Login Feature Implementation Plan

**Objective**: Implement passwordless (email + OTP) login for the Virtual Realtor application.
**Goal**: Allow users to maintain a persistent chat history across devices while preserving their anonymous session context upon sign-in.

---

## 1. Context & Current State

- **Frontend**: Single `index.html` file using Vanilla JS/CSS. No build process.
    - *Path*: `virtual_realtor/frontend/src/index.html`
- **Backend**: FastAPI application serving chat and streaming responses.
    - *Path*: `virtual_realtor/backend/src/app/main.py`
    - *Auth*: Currently relies solely on a `session_id` cookie for anonymous tracking.
- **Infrastructure**: AWS CDK (Python).
    - *Path*: `virtual_realtor/stack.py`
    - *Auth*: Currently has an Admin User Pool, but no Customer User Pool.

---

## 2. Implementation Roadmap

### Phase 1: Infrastructure (AWS Cognito)
We need a dedicated User Pool to manage external customers securely.

- [ ] **Create Customer Auth Construct**
    - Create new file: `virtual_realtor/customer_auth.py`.
    - Define `CustomerAuth` class inheriting from `Construct`.
    - Configure `UserPool`:
        - Name: `vr-customer-user-pool`
        - Self-sign-up: Enabled.
        - Attributes: Email required.
        - Mfa: Optional (using OTP flow).
    - Configure `UserPoolClient`:
        - AuthFlows: `custom=True` (or `USER_AUTH` for OTP).
        - No client secret (for public frontend use).
- [ ] **Update Main Stack**
    - Modify `virtual_realtor/stack.py`.
    - Initialize `CustomerAuth` construct.
    - **Output** the `UserPoolId` and `UserPoolClientId` as CloudFormation outputs (needed for Frontend).
- [ ] **Deploy**
    - Run `uv run cdk deploy --all`.
    - **Capture** the new User Pool ID and Client ID from the output.

> **🛑 CHECKPOINT 1**: Verify the User Pool is created in the AWS Console. Ensure "Sign-up" is allowed.

---

### Phase 2: Backend (Session Merging & Validation)
The backend needs to recognize logged-in users and merge their previous anonymous history.

- [ ] **Add Auth Dependencies**
    - Add `python-jose` and `requests` (if needed for JWKS) to `requirements.txt` / `pyproject.toml`.
- [ ] **Implement Token Validation**
    - Create helper `verify_cognito_token(token)` in `backend/src/app/auth.py`.
    - Should validate signature, issuer, and expiration against the new User Pool.
- [ ] **Update Chat Endpoint (`/api/chat`)**
    - Modify `chat` function signature to accept `Authorization` header (optional).
    - **Logic Change**:
        1. If `Authorization` header exists -> Validate Token -> Get `user_id`.
        2. If `user_id` present:
            - Check if this user already has a session in DB.
            - Check if there is an *active* anonymous cookie (`session_id`).
            - **Merge Logic**: If anonymous session exists & user session exists -> Append anonymous history to user session -> Delete anonymous session reference (or just switch pointer).
            - Use `user_id` as the primary key for `S3SessionManager`.
        3. If no header: Continue using `session_id` cookie (Anonymous mode).
- [ ] **Update Session Manager**
    - Ensure `S3SessionManager` can handle non-UUID keys (if `user_id` format differs) or consistently maps users to storage keys.

> **🛑 CHECKPOINT 2**: Test the API with `curl`.
> 1. Call without token -> Expect normal response (Anonymous).
> 2. Call with valid token -> Expect response (Authenticated).
> 3. Verify in S3/DB that the session file is now associated with the User ID.

---

### Phase 3: Frontend (UI & Integration)
We will add AWS Amplify to handle the complex crypto of SRP/Auth flows without a build step.

- [ ] **Add AWS Amplify**
    - Add Amplify script tag to `index.html` head (CDN).
    - Initialize Amplify at bottom of script:
      ```javascript
      Amplify.configure({
        Auth: {
          Cognito: { userPoolId: '...', userPoolClientId: '...' }
        }
      });
      ```
- [ ] **Build Login UI**
    - Create a "Sign In" button in the `.chat-header`.
    - Create a **Modal Overlay** (hidden by default) containing:
        - "Enter Email" view.
        - "Enter OTP" view.
        - Error/Status message area.
- [ ] **Implement Auth Flow (JS)**
    - `signIn(email)` -> Calls Amplify `signIn`. Handles `CONFIRM_SIGN_IN_WITH_EMAIL_CODE`.
    - `confirm(otp)` -> Calls Amplify `confirmSignIn`.
    - On Success:
        - Save `accessToken` / `idToken`.
        - Close Modal.
        - Update UI to show "Sign Out".
        - **Trigger Merge**: Immediately send a "system" ping or wait for next user message? *Decision: Wait for next message or send silent background request to ensure merge happens immediately.*
- [ ] **Update API Calls**
    - Modify `sendMessage()` function.
    - If `isLoggedIn()`: Add `Authorization: Bearer <token>` header to the `fetch('/api/chat')` call.

> **🛑 CHECKPOINT 3**: Full End-to-End Test.
> 1. Open new browser. Chat anonymously.
> 2. Click Sign In. Login with email/OTP.
> 3. Verify UI updates.
> 4. Send next message.
> 5. Reload page. Verify still logged in and history remains.
> 6. Open different browser, login. Verify history syncs.

---

## 3. Deployment

- [ ] Commit all changes.
- [ ] Deploy backend (if separate from CDK).
- [ ] Deploy frontend (if hosted separately, e.g., S3/CloudFront).

