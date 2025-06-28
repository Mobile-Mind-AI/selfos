<!-- docs/AUTHENTICATION_SETUP.md -->
# Authentication Provider Setup

This document describes how to configure external identity providers for SelfOS.

## Firebase Auth (Google)

SelfOS uses the Firebase Admin SDK to handle user management and authentication. To enable this in your local or staging environment, follow these steps to obtain and configure `GOOGLE_APPLICATION_CREDENTIALS`:

1. Navigate to the Firebase Console:
   https://console.firebase.google.com/

2. Select your project, or create a new one.

3. Go to **Project Settings** (gear icon) → **Service accounts**.

4. Click **Generate new private key**.
   - Confirm the prompt; this will download a JSON file containing your service account credentials.

5. Securely store the downloaded JSON file (e.g., `~/secrets/selfos-firebase.json`).

6. Set the environment variable to point to this file:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/selfos-firebase.json"
   ```

7. (Docker) If running via Docker Compose, mount the file and pass the variable:
   ```yaml
   services:
     backend:
       volumes:
         - ./secrets/selfos-firebase.json:/secrets/selfos-firebase.json:ro
       environment:
         - GOOGLE_APPLICATION_CREDENTIALS=/secrets/selfos-firebase.json
   ```

8. Verify that your backend can initialize the Admin SDK without errors.

## Other Providers (coming soon)
- **Facebook Login**: Use Firebase Auth social provider or configure a custom OAuth2 flow.
- **AWS Cognito**: Integrate via JWT verification against your user pool.
- **GitHub, Apple, etc.**: Configure as OAuth providers in Firebase or via Authlib.

For other identity providers, refer to their respective docs and ensure your backend can verify the issued JWTs.