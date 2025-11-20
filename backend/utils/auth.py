"""
Authentication utilities for JewelTech
JWT token handling, password hashing, and email verification
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.config import settings
from backend.models.mongodb import UserModel, TrialUsageModel
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Security for bearer tokens
security = HTTPBearer()


class AuthUtils:
    """Authentication utility functions"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decode and verify a JWT token"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
            return payload
        except JWTError:
            return None

    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)


class EmailService:
    """Email service for sending verification emails"""

    @staticmethod
    def send_verification_email(email: str, token: str, username: str) -> bool:
        """Send email verification link"""
        try:
            # Email configuration from settings
            smtp_host = settings.smtp_host
            smtp_port = settings.smtp_port
            smtp_user = settings.smtp_user
            smtp_password = settings.smtp_password
            from_email = settings.from_email if settings.from_email else smtp_user
            frontend_url = settings.frontend_url

            if not smtp_user or not smtp_password:
                print("SMTP credentials not configured. Email not sent.")
                return False

            # Create verification link
            verification_link = f"{frontend_url}/verify-email?token={token}"

            # Create email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Verify Your JewelTech Account"
            msg["From"] = from_email
            msg["To"] = email

            # HTML email template
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0;">Welcome to JewelTech!</h1>
                  </div>
                  <div style="padding: 30px; background: #f9f9f9; border-radius: 0 0 10px 10px;">
                    <p style="font-size: 16px;">Hi <strong>{username}</strong>,</p>
                    <p style="font-size: 16px;">Thank you for signing up! Please verify your email address to get started with your <strong>3 free trials</strong> of each feature:</p>

                    <ul style="font-size: 14px; color: #555;">
                      <li>AI Jewelry Designer</li>
                      <li>Virtual Try-On</li>
                      <li>QC Inspector</li>
                      <li>3D Model Generation</li>
                    </ul>

                    <div style="text-align: center; margin: 30px 0;">
                      <a href="{verification_link}"
                         style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
                        Verify Email Address
                      </a>
                    </div>

                    <p style="font-size: 14px; color: #666;">Or copy and paste this link in your browser:</p>
                    <p style="font-size: 12px; color: #999; word-break: break-all;">{verification_link}</p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                    <p style="font-size: 12px; color: #999;">This link will expire in 24 hours. If you didn't create this account, please ignore this email.</p>
                  </div>
                </div>
              </body>
            </html>
            """

            # Plain text fallback
            text = f"""
            Welcome to JewelTech!

            Hi {username},

            Thank you for signing up! Please verify your email address to get started with your 3 free trials.

            Click here to verify: {verification_link}

            This link will expire in 24 hours.
            """

            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            msg.attach(part1)
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            print(f"Verification email sent to {email}")
            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    @staticmethod
    def send_waitlist_confirmation(email: str, username: str, position: int) -> bool:
        """Send waitlist confirmation email"""
        try:
            smtp_host = settings.smtp_host
            smtp_port = settings.smtp_port
            smtp_user = settings.smtp_user
            smtp_password = settings.smtp_password
            from_email = settings.from_email if settings.from_email else smtp_user

            if not smtp_user or not smtp_password:
                print("SMTP credentials not configured. Email not sent.")
                return False

            msg = MIMEMultipart("alternative")
            msg["Subject"] = "You're on the JewelTech Waitlist!"
            msg["From"] = from_email
            msg["To"] = email

            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                  <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0;">You're on the List!</h1>
                  </div>
                  <div style="padding: 30px; background: #f9f9f9; border-radius: 0 0 10px 10px;">
                    <p style="font-size: 16px;">Hi <strong>{username}</strong>,</p>
                    <p style="font-size: 16px;">Thank you for your interest in JewelTech! You're now <strong>#{position}</strong> on our waitlist.</p>

                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
                      <p style="margin: 0; font-size: 14px; color: #555;">
                        <strong>Get Priority Access:</strong> Refer friends and move up the list! Each referral gets you +1 bonus trial.
                      </p>
                    </div>

                    <p style="font-size: 14px; color: #666;">We'll notify you as soon as your unlimited access is ready.</p>

                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                    <p style="font-size: 12px; color: #999;">Questions? Reply to this email or visit our website.</p>
                  </div>
                </div>
              </body>
            </html>
            """

            part = MIMEText(html, "html")
            msg.attach(part)

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Error sending waitlist email: {e}")
            return False


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Dependency to get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = AuthUtils.decode_token(token)

    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = UserModel.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_verified_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Dependency to get current verified user

    Note: current_user is already fresh from database (fetched in get_current_user),
    so this check reflects the latest verification status.
    """
    user_id = current_user.get("_id")
    is_verified = current_user.get("is_verified", False)

    print(f"🔍 Verification check for user {user_id}: is_verified={is_verified}")

    if not is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email to continue."
        )
    return current_user


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Dependency to verify admin access"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def check_trial_limit(
    feature: str,
    current_user: Dict[str, Any] = Depends(get_current_verified_user)
) -> Dict[str, Any]:
    """Middleware to check trial limits before allowing feature access"""
    user_id = current_user["_id"]

    # Check trial limit
    trial_status = TrialUsageModel.check_trial_limit(user_id, feature)

    if not trial_status["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "trial_limit_reached",
                "message": f"You've used all {trial_status['limit']} trials for {feature}. Join our waitlist for unlimited access!",
                "trial_status": trial_status
            }
        )

    # Add trial info to user object
    current_user["trial_status"] = trial_status
    return current_user


def get_client_info(request: Request) -> Dict[str, str]:
    """Extract client information from request"""
    return {
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    }
