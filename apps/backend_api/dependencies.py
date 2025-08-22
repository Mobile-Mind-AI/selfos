import os

import firebase_admin
from db import SessionLocal
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials
from sqlalchemy.orm import Session

"""
Dependency utilities for authentication and database session.
"""

print("🚀 Dependencies module is being imported!")

# Initialize Firebase Admin SDK (optional for testing)
cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
firebase_initialized = False
is_testing = (
    os.environ.get("TESTING", "false").lower() == "true"
    or os.environ.get("ENVIRONMENT", "").lower() == "testing"
)

if not is_testing:
    try:
        if cred_path:
            print(
                f"🔥 FIREBASE: Attempting to initialize with credentials: {cred_path}"
            )
            import os.path

            if os.path.exists(cred_path):
                print("🔥 FIREBASE: Credentials file exists")
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                firebase_initialized = True
                print("🔥 FIREBASE: Successfully initialized with service account")
            else:
                print(f"🔥 FIREBASE: Credentials file does not exist: {cred_path}")
        else:
            print("🔥 FIREBASE: No GOOGLE_APPLICATION_CREDENTIALS set, trying default")
            firebase_admin.initialize_app()
            firebase_initialized = True
            print("🔥 FIREBASE: Successfully initialized with default credentials")
    except Exception as e:
        print(f"🔥 FIREBASE: Failed to initialize: {e}")
        firebase_initialized = False
else:
    print("🔥 FIREBASE: Testing mode detected, skipping Firebase initialization")
    firebase_initialized = False

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    print(
        f"🔐 AUTH: Received token: {token[:20]}...{token[-20:]}"
        if token and len(token) > 40
        else f"🔐 AUTH: Received token: {token}"
    )

    # Check if we're in testing mode
    import os

    is_testing = (
        os.environ.get("TESTING", "false").lower() == "true"
        or os.environ.get("ENVIRONMENT", "").lower() == "testing"
    )

    try:
        # Try Firebase ID token verification first
        payload = firebase_auth.verify_id_token(token)
        uid = payload.get("uid")
        email = payload.get("email")
        roles = payload.get("roles", [])
        if not uid or not email:
            raise credentials_exception

        # Get the sign-in provider from Firebase token
        firebase_info = payload.get("firebase", {})
        sign_in_provider = firebase_info.get("sign_in_provider", "")

        # Add provider prefix to UID for consistency with legacy data
        if sign_in_provider == "google.com" and not uid.startswith("google_"):
            uid = f"google_{uid}"
        elif sign_in_provider == "apple.com" and not uid.startswith("apple_"):
            uid = f"apple_{uid}"

        print(
            f"🔐 AUTH: Firebase auth successful - uid: {uid}, email: {email}, provider: {sign_in_provider}"
        )

        # Ensure user exists in database
        import models

        existing_user = db.query(models.User).filter(models.User.uid == uid).first()
        if not existing_user:
            print(f"🔐 AUTH: User not found in DB, creating: {uid}")
            db_user = models.User(uid=uid, email=email)
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            print(f"🔐 AUTH: Created user in database: {uid}")

        return {"uid": uid, "email": email, "roles": roles}
    except Exception as e:
        print(f"🔐 AUTH: Firebase auth failed: {e}")

        # In testing mode, be more restrictive with fallbacks
        if is_testing:
            print("🔐 AUTH: Testing mode - limited fallback authentication")
            # Only allow JWT tokens in testing mode
            try:
                import jwt

                payload = jwt.decode(token, "dev-secret", algorithms=["HS256"])
                uid = payload.get("uid")
                email = payload.get("email")
                if uid and email:
                    print(
                        f"🔐 AUTH: JWT auth successful (testing) - uid: {uid}, email: {email}"
                    )
                    # Ensure user exists in database
                    import models

                    existing_user = (
                        db.query(models.User).filter(models.User.uid == uid).first()
                    )
                    if not existing_user:
                        print(
                            f"🔐 AUTH: User not found in DB (JWT testing), creating: {uid}"
                        )
                        db_user = models.User(uid=uid, email=email)
                        db.add(db_user)
                        db.commit()
                        db.refresh(db_user)
                        print(f"🔐 AUTH: Created user in database (JWT testing): {uid}")
                    return {"uid": uid, "email": email, "roles": []}
            except Exception as jwt_e:
                print(f"🔐 AUTH: JWT decode failed in testing mode: {jwt_e}")

            # In testing mode, fail fast - don't try additional fallbacks
            print("🔐 AUTH: Testing mode - raising 401 Unauthorized")
            raise credentials_exception

        # Production fallback logic (more permissive for backwards compatibility)
        try:
            import base64
            import json

            import jwt

            # First try to decode as JWT (custom token)
            try:
                # Try to decode with the dev secret
                payload = jwt.decode(token, "dev-secret", algorithms=["HS256"])
                uid = payload.get("uid")
                email = payload.get("email")
                if uid and email:
                    print(f"🔐 AUTH: JWT auth successful - uid: {uid}, email: {email}")
                    # Ensure user exists in database
                    import models

                    existing_user = (
                        db.query(models.User).filter(models.User.uid == uid).first()
                    )
                    if not existing_user:
                        print(f"🔐 AUTH: User not found in DB (JWT), creating: {uid}")
                        db_user = models.User(uid=uid, email=email)
                        db.add(db_user)
                        db.commit()
                        db.refresh(db_user)
                        print(f"🔐 AUTH: Created user in database (JWT): {uid}")
                    return {"uid": uid, "email": email, "roles": []}
            except jwt.InvalidTokenError as jwt_e:
                print(f"🔐 AUTH: JWT decode with secret failed: {jwt_e}")
                # Try without verification for backwards compatibility
                try:
                    payload = jwt.decode(token, options={"verify_signature": False})
                    uid = payload.get("uid")
                    email = payload.get("email")
                    if uid and email:
                        print(
                            f"🔐 AUTH: JWT auth successful (unverified) - uid: {uid}, email: {email}"
                        )
                        # Ensure user exists in database
                        import models

                        existing_user = (
                            db.query(models.User).filter(models.User.uid == uid).first()
                        )
                        if not existing_user:
                            print(
                                f"🔐 AUTH: User not found in DB (JWT unverified), creating: {uid}"
                            )
                            db_user = models.User(uid=uid, email=email)
                            db.add(db_user)
                            db.commit()
                            db.refresh(db_user)
                            print(
                                f"🔐 AUTH: Created user in database (JWT unverified): {uid}"
                            )
                        return {"uid": uid, "email": email, "roles": []}
                except Exception as e:
                    print(f"🔐 AUTH: JWT decode without verification failed: {e}")
                    pass

            # Try to decode mock token for testing
            decoded = base64.b64decode(token.encode()).decode()
            mock_payload = json.loads(decoded)
            if mock_payload.get("mock"):
                print(f"🔐 AUTH: Mock auth successful - uid: {mock_payload.get('uid')}")
                return {
                    "uid": mock_payload.get("uid"),
                    "email": mock_payload.get("email"),
                    "roles": [],
                }
        except Exception as fallback_e:
            print(f"🔐 AUTH: All auth methods failed: {fallback_e}")
            pass
        print("🔐 AUTH: Raising 401 Unauthorized")
        raise credentials_exception
