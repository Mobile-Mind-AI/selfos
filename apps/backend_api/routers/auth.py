from fastapi import APIRouter, Depends, HTTPException, status
from schemas import RegisterRequest, LoginRequest, TokenResponse
from firebase_admin import auth as firebase_auth
from dependencies import get_current_user


router = APIRouter()


@router.post("/register")
async def register(req: RegisterRequest):
    """
    Create a new user in Firebase Auth and return their UID and email.
    """
    try:
        user = firebase_auth.create_user(email=req.username, password=req.password)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"uid": user.uid, "email": user.email}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """
    Issue a custom Firebase Auth token for the given user UID.
    """
    try:
        custom_token = firebase_auth.create_custom_token(req.username)
        token_str = custom_token.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return TokenResponse(access_token=token_str)


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    """
    Return the current authenticated user's UID, email, and roles.
    """
    return current_user
