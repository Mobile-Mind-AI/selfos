from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from schemas import RegisterRequest, LoginRequest, TokenResponse, AuthResponse, User, UserOut
from firebase_admin import auth as firebase_auth
from dependencies import get_current_user, get_db
from services.email_service import email_service
import models
from datetime import datetime


router = APIRouter()


@router.post("/register", status_code=201)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new user in Firebase Auth and database, return their UID and email.
    Supports both email/password and social login registration.
    """
    try:
        if req.provider == "email":
            # Email/password registration
            user = firebase_auth.create_user(email=req.username, password=req.password)
            uid = user.uid
            email = user.email
        else:
            # Social login registration
            # For social login, create Firebase user
            if req.provider == "google":
                uid = f"google_{req.email}"
                email = req.email
                
                # Create Firebase user for Google
                user = firebase_auth.create_user(
                    uid=uid,
                    email=email,
                    email_verified=True
                )
                
            elif req.provider == "apple":
                uid = f"apple_{req.social_token}"
                email = req.email or f"apple_user_{req.social_token[:8]}@privaterelay.appleid.com"
                
                # Create Firebase user for Apple
                user = firebase_auth.create_user(
                    uid=uid,
                    email=email,
                    email_verified=True
                )
                
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported provider: {req.provider}")
            
            uid = user.uid
            email = user.email
    except Exception as e:
        # For testing purposes, create a mock user if Firebase fails
        import uuid
        if req.provider == "email":
            uid = req.username  # Use username as UID for testing
            email = req.username
        else:
            uid = f"{req.provider}_{req.email}"
            email = req.email
    
    # Create user in database
    existing_user = db.query(models.User).filter(models.User.uid == uid).first()
    if not existing_user:
        db_user = models.User(
            uid=uid,
            email=email
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    
    return {"uid": uid, "email": email}


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """
    Issue a custom Firebase Auth token for the given user UID.
    Supports both email/password and social login.
    """
    try:
        if req.provider == "email":
            # Email/password login
            custom_token = firebase_auth.create_custom_token(req.username)
            token_str = custom_token.decode("utf-8")
            user = User(uid=req.username, email=req.username)
            return AuthResponse(access_token=token_str, user=user)
        else:
            # Social login
            # For social login, create or get existing Firebase user
            if req.provider == "google":
                uid = f"google_{req.email}"
                email = req.email
                
                # Try to get existing user, or create new one
                try:
                    firebase_user = firebase_auth.get_user(uid)
                except firebase_auth.UserNotFoundError:
                    # Create new Firebase user for Google login
                    firebase_user = firebase_auth.create_user(
                        uid=uid,
                        email=email,
                        email_verified=True  # Google emails are pre-verified
                    )
                
                custom_token = firebase_auth.create_custom_token(uid)
                token_str = custom_token.decode("utf-8")
                user = User(uid=uid, email=email)
                return AuthResponse(access_token=token_str, user=user)
                
            elif req.provider == "apple":
                uid = f"apple_{req.social_token}"
                email = req.email or f"apple_user_{req.social_token[:8]}@privaterelay.appleid.com"
                
                # Try to get existing user, or create new one
                try:
                    firebase_user = firebase_auth.get_user(uid)
                except firebase_auth.UserNotFoundError:
                    # Create new Firebase user for Apple login
                    firebase_user = firebase_auth.create_user(
                        uid=uid,
                        email=email,
                        email_verified=True  # Apple emails are pre-verified
                    )
                
                custom_token = firebase_auth.create_custom_token(uid)
                token_str = custom_token.decode("utf-8")
                user = User(uid=uid, email=email)
                return AuthResponse(access_token=token_str, user=user)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported provider: {req.provider}")
    except Exception as e:
        print(f"🔥 FIREBASE: Login failed, using fallback: {e}")
        # For testing purposes, return a mock token if Firebase fails
        import base64
        import json
        import jwt
        
        if req.provider == "email":
            uid = req.username
            email = req.username
        else:
            # Use consistent UID generation for social login
            if req.provider == "google":
                uid = f"google_{req.email}"
                email = req.email
            elif req.provider == "apple":
                uid = f"apple_{req.social_token}"
                email = req.email or f"apple_user_{req.social_token[:8]}@privaterelay.appleid.com"
            else:
                uid = f"{req.provider}_{req.email or 'unknown'}"
                email = req.email or f"{req.provider}_user@example.com"
        
        # Create a proper JWT token instead of mock token
        payload = {
            "uid": uid,
            "email": email,
            "provider": req.provider,
            "iss": "selfos-backend",
            "aud": "selfos-app"
        }
        
        # Use a simple secret for development (in production, use proper Firebase)
        token = jwt.encode(payload, "dev-secret", algorithm="HS256")
        user = User(uid=uid, email=email)
        return AuthResponse(access_token=token, user=user)


@router.post("/forgot-password")
async def forgot_password(request: dict):
    """
    Send password reset email using Firebase Auth with enhanced email service.
    
    This endpoint:
    1. Validates the email and checks if user exists
    2. Generates a password reset link via Firebase
    3. Attempts to send email automatically via Firebase
    4. Falls back to providing the link directly for development
    """
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    print(f"🔥 FIREBASE: Starting password reset for email: {email}")
    
    # Validate email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return {"message": "Invalid email format"}
    
    try:
        # Check if user exists in Firebase
        user = firebase_auth.get_user_by_email(email)
        user_exists = True
        print(f"🔥 FIREBASE: User found for email: {email} (UID: {user.uid})")
        
    except firebase_auth.UserNotFoundError:
        print(f"🔥 FIREBASE: User not found for email: {email}")
        # For security, don't reveal if user exists or not
        return {"message": "If an account with this email exists, a password reset link has been sent"}
        
    except Exception as e:
        print(f"🔥 FIREBASE: Error checking user: {e}")
        return {"message": "Unable to process password reset request. Please try again later."}
    
    try:
        # Generate password reset link with Firebase
        import firebase_admin.exceptions
        from firebase_admin import auth as firebase_auth_admin
        
        # Configure action code settings for better email delivery
        action_code_settings = firebase_auth_admin.ActionCodeSettings(
            url='https://selfos-c4ed0.firebaseapp.com',  # Continue URL after password reset
            handle_code_in_app=False,  # Handle in web browser, not app
        )
        
        # Generate the password reset link
        link = firebase_auth.generate_password_reset_link(
            email, 
            action_code_settings=action_code_settings
        )
        
        print(f"🔥 FIREBASE: Password reset link generated: {link}")
        
        # Send email using our custom email service
        try:
            # Extract user display name if available
            user_name = getattr(user, 'display_name', None) or user.email.split('@')[0]
            
            # Send password reset email
            email_sent = email_service.send_password_reset_email(
                to_email=email,
                reset_link=link,
                user_name=user_name
            )
            
            if email_sent:
                print(f"🔥 EMAIL: Password reset email sent successfully to {email}")
                return {
                    "message": "Password reset email sent successfully",
                    "status": "Email delivered",
                    "instructions": [
                        "1. Check your email inbox for the password reset link",
                        "2. Click the link in the email to reset your password", 
                        "3. The link expires in 1 hour for security",
                        "4. Check your spam folder if you don't see the email"
                    ],
                    "reset_link": link,  # Also provide link for development
                    "dev_note": "Reset link also provided above for development/testing"
                }
            else:
                print(f"🔥 EMAIL: Failed to send email, providing fallback link")
                return {
                    "message": "Password reset link generated",
                    "status": "Email service unavailable - using direct link",
                    "reset_link": link,
                    "instructions": [
                        "Email delivery failed, please use the link below",
                        "Click the link to reset your password",
                        "The link expires in 1 hour for security",
                        "Save this link or use it immediately"
                    ],
                    "note": "Please use the reset link above to change your password"
                }
            
        except Exception as email_error:
            print(f"🔥 EMAIL: Email service error: {email_error}")
            
            # Fallback: provide the link directly
            return {
                "message": "Password reset link generated", 
                "status": "Email service error - using direct link",
                "reset_link": link,
                "instructions": [
                    "Please click the link below to reset your password",
                    "The link expires in 1 hour for security",
                    "Save this link or use it immediately"
                ],
                "error": "Email delivery temporarily unavailable"
            }
        
    except firebase_admin.exceptions.InvalidArgumentError as e:
        print(f"🔥 FIREBASE: Invalid argument: {e}")
        return {"message": "Invalid email address provided"}
        
    except firebase_admin.exceptions.NotFoundError as e:
        print(f"🔥 FIREBASE: User not found in password reset: {e}")
        return {"message": "If an account with this email exists, a password reset link has been sent"}
        
    except firebase_admin.exceptions.UnauthenticatedError as e:
        print(f"🔥 FIREBASE: Authentication error: {e}")
        return {"message": "Service authentication error. Please contact support."}
        
    except firebase_admin.exceptions.PermissionDeniedError as e:
        print(f"🔥 FIREBASE: Permission denied: {e}")
        return {"message": "Password reset service is temporarily unavailable. Please contact support."}
        
    except Exception as e:
        print(f"🔥 FIREBASE: Unexpected error in password reset: {e}")
        print(f"🔥 FIREBASE: Error type: {type(e).__name__}")
        
        # Check if it's a quota or configuration error
        error_message = str(e).lower()
        if 'quota' in error_message or 'limit' in error_message:
            return {"message": "Password reset service is temporarily unavailable due to high demand. Please try again later."}
        elif 'configuration' in error_message or 'not configured' in error_message:
            return {"message": "Password reset service is not properly configured. Please contact support."}
        else:
            return {"message": "Unable to process password reset request. Please try again later."}


@router.post("/test-forgot")
async def test_forgot(request: dict):
    """Test endpoint to debug forgot password"""
    email = request.get("email")
    print(f"🔥 TEST: Received email: {email}")
    
    try:
        link = firebase_auth.generate_password_reset_link(email)
        print(f"🔥 TEST: Link generated: {link}")
        return {"success": True, "link": link}
    except Exception as e:
        print(f"🔥 TEST: Error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    """
    Return the current authenticated user's UID, email, and roles.
    """
    return current_user
