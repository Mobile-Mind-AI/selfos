from fastapi import FastAPI
from pydantic import BaseModel

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
    # TODO: implement user creation in database
    return {"message": f"User '{req.username}' registered (stub)"}

@app.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    # TODO: authenticate user and generate JWT
    fake_token = "fake.jwt.token"
    return TokenResponse(access_token=fake_token)

@app.get("/me")
async def me():
    # TODO: extract user from JWT
    return {"username": "current_user_stub"}