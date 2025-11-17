"""
MongoDB Models for GemVision
User authentication, trial tracking, and waitlist management
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from backend.app.config import settings
import os

# MongoDB connection - Use Atlas if configured, otherwise local
MONGO_ATLAS_URI = os.getenv("MONGO_ATLAS_URI", "")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "gemvision")
MONGO_ATLAS_DB_NAME = os.getenv("MONGO_ATLAS_DB_NAME", "gemvision")

# Use Atlas URI if available, otherwise fall back to local
ACTIVE_MONGO_URL = MONGO_ATLAS_URI if MONGO_ATLAS_URI else MONGODB_URL
ACTIVE_DB_NAME = MONGO_ATLAS_DB_NAME if MONGO_ATLAS_URI else MONGODB_DB_NAME

client: Optional[MongoClient] = None
db: Optional[Database] = None


def get_mongodb():
    """Get MongoDB database instance"""
    global client, db
    if client is None:
        print(f"Connecting to MongoDB: {'Atlas' if MONGO_ATLAS_URI else 'Local'}")
        client = MongoClient(ACTIVE_MONGO_URL)
        db = client[ACTIVE_DB_NAME]
        init_mongodb_indexes()
        print(f"MongoDB connected successfully to database: {ACTIVE_DB_NAME}")
    return db


def init_mongodb_indexes():
    """Initialize MongoDB indexes for performance"""
    global db
    if db is None:
        return

    # Users collection indexes
    db.users.create_index([("email", ASCENDING)], unique=True)
    db.users.create_index([("username", ASCENDING)], unique=True)
    db.users.create_index([("phone", ASCENDING)], sparse=True)
    db.users.create_index([("created_at", DESCENDING)])
    db.users.create_index([("is_active", ASCENDING)])

    # Waitlist collection indexes
    db.waitlist.create_index([("user_id", ASCENDING)])
    db.waitlist.create_index([("email", ASCENDING)])
    db.waitlist.create_index([("joined_at", DESCENDING)])
    db.waitlist.create_index([("status", ASCENDING)])

    # Trial usage collection indexes
    db.trial_usage.create_index([("user_id", ASCENDING)])
    db.trial_usage.create_index([("feature", ASCENDING)])
    db.trial_usage.create_index([("timestamp", DESCENDING)])

    # Email verification tokens
    db.verification_tokens.create_index([("token", ASCENDING)], unique=True)
    db.verification_tokens.create_index([("email", ASCENDING)])
    db.verification_tokens.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)  # TTL index


class UserModel:
    """User model operations"""

    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user"""
        db = get_mongodb()

        # Default user structure
        user = {
            "email": user_data["email"],
            "username": user_data["username"],
            "password_hash": user_data["password_hash"],
            "phone": user_data.get("phone"),
            "full_name": user_data.get("full_name"),
            "role": user_data.get("role", "trial"),  # trial, unlimited, admin
            "is_active": True,
            "is_verified": False,
            "is_admin": user_data.get("is_admin", False),
            "created_at": datetime.utcnow(),
            "last_login": None,
            "trial_limits": {
                "ai_designer": {"used": 0, "limit": 3},
                "virtual_tryon": {"used": 0, "limit": 3},
                "qc_inspector": {"used": 0, "limit": 3},
                "3d_generation": {"used": 0, "limit": 3}
            },
            "metadata": {
                "signup_ip": user_data.get("signup_ip"),
                "user_agent": user_data.get("user_agent"),
                "referral_code": user_data.get("referral_code"),
                "referred_by": user_data.get("referred_by")
            }
        }

        result = db.users.insert_one(user)
        user["_id"] = str(result.inserted_id)
        return user

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        db = get_mongodb()
        user = db.users.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user

    @staticmethod
    def get_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        db = get_mongodb()
        user = db.users.find_one({"username": username})
        if user:
            user["_id"] = str(user["_id"])
        return user

    @staticmethod
    def get_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        db = get_mongodb()
        from bson import ObjectId
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
        return user

    @staticmethod
    def update_user(user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        db = get_mongodb()
        from bson import ObjectId
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    @staticmethod
    def verify_email(email: str) -> bool:
        """Mark user email as verified"""
        db = get_mongodb()
        result = db.users.update_one(
            {"email": email},
            {"$set": {"is_verified": True, "verified_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    @staticmethod
    def update_last_login(user_id: str) -> bool:
        """Update last login timestamp"""
        db = get_mongodb()
        from bson import ObjectId
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        return result.modified_count > 0


class TrialUsageModel:
    """Trial usage tracking operations"""

    @staticmethod
    def record_usage(user_id: str, feature: str) -> Dict[str, Any]:
        """Record a feature usage"""
        db = get_mongodb()

        usage_record = {
            "user_id": user_id,
            "feature": feature,
            "timestamp": datetime.utcnow()
        }

        result = db.trial_usage.insert_one(usage_record)

        # Update user's trial counter
        from bson import ObjectId
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {f"trial_limits.{feature}.used": 1}}
        )

        usage_record["_id"] = str(result.inserted_id)
        return usage_record

    @staticmethod
    def get_user_usage(user_id: str, feature: Optional[str] = None) -> list:
        """Get usage history for a user"""
        db = get_mongodb()

        query = {"user_id": user_id}
        if feature:
            query["feature"] = feature

        usage = list(db.trial_usage.find(query).sort("timestamp", DESCENDING))
        for record in usage:
            record["_id"] = str(record["_id"])
        return usage

    @staticmethod
    def check_trial_limit(user_id: str, feature: str) -> Dict[str, Any]:
        """Check if user has remaining trials for a feature"""
        user = UserModel.get_by_id(user_id)
        if not user:
            return {"allowed": False, "reason": "User not found"}

        # Check if user has unlimited access
        if user.get("role") == "unlimited" or user.get("is_admin"):
            return {"allowed": True, "remaining": -1, "unlimited": True}

        # Check trial limits
        trial_limits = user.get("trial_limits", {})
        feature_limit = trial_limits.get(feature, {"used": 0, "limit": 3})

        used = feature_limit.get("used", 0)
        limit = feature_limit.get("limit", 3)
        remaining = limit - used

        return {
            "allowed": remaining > 0,
            "used": used,
            "limit": limit,
            "remaining": max(0, remaining),
            "unlimited": False
        }

    @staticmethod
    def add_bonus_trial(user_id: str, feature: str, bonus: int = 1) -> bool:
        """Add bonus trials to a user (e.g., from referrals)"""
        db = get_mongodb()
        from bson import ObjectId
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {f"trial_limits.{feature}.limit": bonus}}
        )
        return result.modified_count > 0


class WaitlistModel:
    """Waitlist management operations"""

    @staticmethod
    def add_to_waitlist(user_id: str, email: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add user to waitlist"""
        db = get_mongodb()

        # Check if already in waitlist
        existing = db.waitlist.find_one({"user_id": user_id})
        if existing:
            existing["_id"] = str(existing["_id"])
            return existing

        waitlist_entry = {
            "user_id": user_id,
            "email": email,
            "full_name": user_data.get("full_name"),
            "phone": user_data.get("phone"),
            "username": user_data.get("username"),
            "joined_at": datetime.utcnow(),
            "status": "pending",  # pending, approved, rejected
            "trial_usage_summary": user_data.get("trial_usage_summary", {}),
            "metadata": {
                "user_agent": user_data.get("user_agent"),
                "referrals_made": user_data.get("referrals_made", 0)
            }
        }

        result = db.waitlist.insert_one(waitlist_entry)
        waitlist_entry["_id"] = str(result.inserted_id)
        return waitlist_entry

    @staticmethod
    def get_waitlist(status: Optional[str] = None, limit: int = 100) -> list:
        """Get waitlist entries"""
        db = get_mongodb()

        query = {}
        if status:
            query["status"] = status

        entries = list(db.waitlist.find(query).sort("joined_at", ASCENDING).limit(limit))
        for entry in entries:
            entry["_id"] = str(entry["_id"])
        return entries

    @staticmethod
    def get_waitlist_count() -> int:
        """Get total waitlist count"""
        db = get_mongodb()
        return db.waitlist.count_documents({})

    @staticmethod
    def is_in_waitlist(user_id: str) -> bool:
        """Check if user is in waitlist"""
        db = get_mongodb()
        return db.waitlist.find_one({"user_id": user_id}) is not None


class VerificationTokenModel:
    """Email verification token operations"""

    @staticmethod
    def create_token(email: str, token: str, expires_in_hours: int = 24) -> Dict[str, Any]:
        """Create a verification token"""
        db = get_mongodb()

        token_data = {
            "email": email,
            "token": token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=expires_in_hours),
            "used": False
        }

        result = db.verification_tokens.insert_one(token_data)
        token_data["_id"] = str(result.inserted_id)
        return token_data

    @staticmethod
    def verify_token(token: str) -> Optional[str]:
        """Verify token and return email if valid"""
        db = get_mongodb()

        token_data = db.verification_tokens.find_one({
            "token": token,
            "used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })

        if token_data:
            # Mark token as used
            db.verification_tokens.update_one(
                {"_id": token_data["_id"]},
                {"$set": {"used": True, "used_at": datetime.utcnow()}}
            )
            return token_data["email"]

        return None

    @staticmethod
    def delete_expired_tokens():
        """Clean up expired tokens (handled by TTL index)"""
        pass


def init_admin_user():
    """Initialize the hardcoded admin user (lakshitaa)"""
    try:
        import bcrypt

        print("[DEBUG] Checking for admin user 'lakshitaa'...")

        # Check if admin user exists
        admin = UserModel.get_by_username("lakshitaa")

        if not admin:
            print("[DEBUG] Admin user not found. Creating...")

            # Hash password with bcrypt directly
            password = "Lakshitaa@2112".encode('utf-8')
            password_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

            admin_data = {
                "email": "lakshitaa@gemvision.com",
                "username": "lakshitaa",
                "password_hash": password_hash,
                "full_name": "Lakshitaa",
                "role": "unlimited",
                "is_admin": True,
                "is_verified": True
            }

            print("[DEBUG] Calling UserModel.create_user...")
            result = UserModel.create_user(admin_data)
            print(f"[SUCCESS] Admin user 'lakshitaa' created successfully!")
            print(f"   Email: lakshitaa@gemvision.com")
            print(f"   Password: Lakshitaa@2112")
            print(f"   User ID: {result.get('_id', 'N/A')}")
        else:
            print(f"[INFO] Admin user 'lakshitaa' already exists (ID: {admin.get('_id', 'N/A')})")

    except Exception as e:
        print(f"[ERROR] Failed to initialize admin user: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Initialize database and create admin user
    get_mongodb()
    init_admin_user()
    print("MongoDB initialized successfully!")
