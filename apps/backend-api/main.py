import os
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin SDK (skip if credentials are missing/invalid)
cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
try:
    if cred_path:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()
except Exception:
    # No valid credentials available (e.g., during testing)
    pass

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = auth.verify_id_token(token)
        uid = payload.get("uid")
        email = payload.get("email")
        roles = payload.get("roles", [])
        if not uid or not email:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    return {"uid": uid, "email": email, "roles": roles}

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "SelfOS Backend API"}
 
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@app.post("/register")
async def register(req: RegisterRequest):
    # Create user in Firebase Auth
    try:
        user = auth.create_user(email=req.username, password=req.password)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"uid": user.uid, "email": user.email}

@app.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    # Generate Firebase custom token for given UID (username)
    try:
        custom_token = auth.create_custom_token(req.username)
        token_str = custom_token.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return TokenResponse(access_token=token_str)

@app.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    # Return current authenticated user
    return current_user