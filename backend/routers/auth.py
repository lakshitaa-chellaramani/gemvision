"""
Authentication Router for GemVision
Handles user signup, login, email verification, and profile management
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import timedelta
from backend.models.mongodb import UserModel, VerificationTokenModel, TrialUsageModel
from backend.utils.auth import (
    AuthUtils, EmailService, get_current_user,
    get_current_verified_user, get_client_info
)
from backend.app.config import settings
import re

router = APIRouter()


# Pydantic models for request/response
class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        # Remove common formatting
        cleaned = re.sub(r'[^\d+]', '', v)
        if len(cleaned) < 10:
            raise ValueError('Invalid phone number')
        return cleaned


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class UserProfileResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    phone: Optional[str]
    role: str
    is_verified: bool
    is_admin: bool
    created_at: str
    trial_limits: dict


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(signup_data: SignupRequest, request: Request):
    """
    Create a new user account with email verification
    """
    # Check if user already exists
    existing_user = UserModel.get_by_email(signup_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    existing_username = UserModel.get_by_username(signup_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken"
        )

    # Get client info
    client_info = get_client_info(request)

    # Create user
    hashed_password = AuthUtils.hash_password(signup_data.password)
    user_data = {
        "email": signup_data.email,
        "username": signup_data.username,
        "password_hash": hashed_password,
        "full_name": signup_data.full_name,
        "phone": signup_data.phone,
        "signup_ip": client_info["ip"],
        "user_agent": client_info["user_agent"]
    }

    user = UserModel.create_user(user_data)

    # Generate verification token
    verification_token = AuthUtils.generate_verification_token()
    VerificationTokenModel.create_token(signup_data.email, verification_token)

    # Send verification email (non-blocking)
    EmailService.send_verification_email(
        signup_data.email,
        verification_token,
        signup_data.username
    )

    # Create access token
    access_token = AuthUtils.create_access_token(
        data={"sub": user["_id"], "email": user["email"]}
    )

    # Remove sensitive data
    user.pop("password_hash", None)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    Authenticate user and return access token
    """
    # Get user
    user = UserModel.get_by_email(login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Verify password
    if not AuthUtils.verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if account is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )

    # Update last login
    UserModel.update_last_login(user["_id"])

    # Create access token
    access_token = AuthUtils.create_access_token(
        data={"sub": user["_id"], "email": user["email"]}
    )

    # Remove sensitive data
    user.pop("password_hash", None)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/verify-email")
async def verify_email(verify_data: VerifyEmailRequest):
    """
    Verify user email with token
    """
    # Verify token
    email = VerificationTokenModel.verify_token(verify_data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    # Mark email as verified
    success = UserModel.verify_email(email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {
        "message": "Email verified successfully!",
        "email": email
    }


@router.post("/resend-verification")
async def resend_verification(resend_data: ResendVerificationRequest):
    """
    Resend verification email
    """
    # Get user
    user = UserModel.get_by_email(resend_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already verified
    if user.get("is_verified", False):
        return {
            "message": "Email already verified"
        }

    # Generate new token
    verification_token = AuthUtils.generate_verification_token()
    VerificationTokenModel.create_token(resend_data.email, verification_token)

    # Send email
    EmailService.send_verification_email(
        resend_data.email,
        verification_token,
        user["username"]
    )

    return {
        "message": "Verification email sent successfully"
    }


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile
    """
    # Remove sensitive data
    current_user.pop("password_hash", None)

    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "username": current_user["username"],
        "full_name": current_user.get("full_name"),
        "phone": current_user.get("phone"),
        "role": current_user.get("role", "trial"),
        "is_verified": current_user.get("is_verified", False),
        "is_admin": current_user.get("is_admin", False),
        "created_at": current_user["created_at"].isoformat(),
        "trial_limits": current_user.get("trial_limits", {})
    }


@router.get("/trial-status")
async def get_trial_status(current_user: dict = Depends(get_current_verified_user)):
    """
    Get user's trial usage status for all features
    """
    user_id = current_user["_id"]
    features = ["ai_designer", "virtual_tryon", "qc_inspector", "3d_generation"]

    trial_status = {}
    for feature in features:
        status_info = TrialUsageModel.check_trial_limit(user_id, feature)
        trial_status[feature] = status_info

    return {
        "user_id": user_id,
        "username": current_user["username"],
        "role": current_user.get("role", "trial"),
        "trial_status": trial_status
    }


@router.post("/logout")
async def logout():
    """
    Logout user (client should remove token)
    """
    return {
        "message": "Logged out successfully"
    }


@router.get("/check-username/{username}")
async def check_username_availability(username: str):
    """
    Check if username is available
    """
    user = UserModel.get_by_username(username)
    return {
        "available": user is None,
        "username": username
    }


@router.get("/check-email/{email}")
async def check_email_availability(email: str):
    """
    Check if email is available
    """
    user = UserModel.get_by_email(email)
    return {
        "available": user is None,
        "email": email
    }
