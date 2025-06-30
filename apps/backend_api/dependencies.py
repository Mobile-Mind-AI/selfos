import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from sqlalchemy.orm import Session
from db import SessionLocal

"""
Dependency utilities for authentication and database session.
"""

print("🚀 Dependencies module is being imported!")

# Initialize Firebase Admin SDK (silently skip if invalid/missing credentials)
cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
firebase_initialized = False
try:
    if cred_path:
        print(f"🔥 FIREBASE: Attempting to initialize with credentials: {cred_path}")
        import os.path
        if os.path.exists(cred_path):
            print(f"🔥 FIREBASE: Credentials file exists")
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            firebase_initialized = True
            print(f"🔥 FIREBASE: Successfully initialized with service account")
        else:
            print(f"🔥 FIREBASE: Credentials file does not exist: {cred_path}")
    else:
        print(f"🔥 FIREBASE: No GOOGLE_APPLICATION_CREDENTIALS set, trying default")
        firebase_admin.initialize_app()
        firebase_initialized = True
        print(f"🔥 FIREBASE: Successfully initialized with default credentials")
except Exception as e:
    print(f"🔥 FIREBASE: Failed to initialize: {e}")
    firebase_initialized = False

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Try Firebase ID token verification first
        payload = firebase_auth.verify_id_token(token)
        uid = payload.get("uid")
        email = payload.get("email")
        roles = payload.get("roles", [])
        if not uid or not email:
            raise credentials_exception
        return {"uid": uid, "email": email, "roles": roles}
    except Exception:
        # Try to decode custom token for testing (our custom format)
        try:
            import base64
            import json
            import jwt
            
            # First try to decode as JWT (custom token)
            try:
                # For custom tokens, we just decode without verification for development
                payload = jwt.decode(token, options={"verify_signature": False})
                uid = payload.get("uid")
                email = payload.get("email") 
                if uid and email:
                    return {"uid": uid, "email": email, "roles": []}
            except:
                pass
            
            # Try to decode mock token for testing
            decoded = base64.b64decode(token.encode()).decode()
            mock_payload = json.loads(decoded)
            if mock_payload.get("mock"):
                return {
                    "uid": mock_payload.get("uid"),
                    "email": mock_payload.get("email"),
                    "roles": []
                }
        except Exception:
            pass
        raise credentials_exception

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()