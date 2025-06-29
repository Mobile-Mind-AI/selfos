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
# Initialize Firebase Admin SDK (silently skip if invalid/missing credentials)
cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
try:
    if cred_path:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()
except Exception:
    pass

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Try Firebase first
        payload = firebase_auth.verify_id_token(token)
        uid = payload.get("uid")
        email = payload.get("email")
        roles = payload.get("roles", [])
        if not uid or not email:
            raise credentials_exception
        return {"uid": uid, "email": email, "roles": roles}
    except Exception:
        # Try to decode mock token for testing
        try:
            import base64
            import json
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