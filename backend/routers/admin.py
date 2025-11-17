"""
Admin Dashboard Router for GemVision
Admin-only endpoints for user management and analytics
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from backend.models.mongodb import UserModel, WaitlistModel, TrialUsageModel, get_mongodb
from backend.utils.auth import get_admin_user
from bson import ObjectId

router = APIRouter()


class UserUpdateRequest(BaseModel):
    role: Optional[str] = None  # trial, unlimited, admin
    is_active: Optional[bool] = None
    trial_limits: Optional[dict] = None


class DashboardStats(BaseModel):
    total_users: int
    verified_users: int
    trial_users: int
    unlimited_users: int
    waitlist_count: int
    total_generations_today: int
    total_tryons_today: int
    total_qc_inspections_today: int


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(admin_user: dict = Depends(get_admin_user)):
    """
    Get dashboard statistics (Admin only)
    """
    db = get_mongodb()

    # User counts
    total_users = db.users.count_documents({})
    verified_users = db.users.count_documents({"is_verified": True})
    trial_users = db.users.count_documents({"role": "trial"})
    unlimited_users = db.users.count_documents({"role": "unlimited"})

    # Waitlist count
    waitlist_count = WaitlistModel.get_waitlist_count()

    # Today's activity
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    total_generations_today = db.trial_usage.count_documents({
        "feature": "ai_designer",
        "timestamp": {"$gte": today_start}
    })

    total_tryons_today = db.trial_usage.count_documents({
        "feature": "virtual_tryon",
        "timestamp": {"$gte": today_start}
    })

    total_qc_inspections_today = db.trial_usage.count_documents({
        "feature": "qc_inspector",
        "timestamp": {"$gte": today_start}
    })

    return {
        "total_users": total_users,
        "verified_users": verified_users,
        "trial_users": trial_users,
        "unlimited_users": unlimited_users,
        "waitlist_count": waitlist_count,
        "total_generations_today": total_generations_today,
        "total_tryons_today": total_tryons_today,
        "total_qc_inspections_today": total_qc_inspections_today
    }


@router.get("/users")
async def get_all_users(
    admin_user: dict = Depends(get_admin_user),
    skip: int = 0,
    limit: int = 50,
    role: Optional[str] = None,
    verified: Optional[bool] = None
):
    """
    Get all users with filtering (Admin only)
    """
    db = get_mongodb()

    # Build query
    query = {}
    if role:
        query["role"] = role
    if verified is not None:
        query["is_verified"] = verified

    # Get users
    users = list(
        db.users.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    # Convert ObjectId to string and remove password
    for user in users:
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)

    total = db.users.count_documents(query)

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "users": users
    }


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get detailed user information (Admin only)
    """
    user = UserModel.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get usage history
    usage_history = TrialUsageModel.get_user_usage(user_id)

    # Check waitlist status
    in_waitlist = WaitlistModel.is_in_waitlist(user_id)

    # Remove password
    user.pop("password_hash", None)

    return {
        "user": user,
        "usage_history": usage_history,
        "in_waitlist": in_waitlist
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: UserUpdateRequest,
    admin_user: dict = Depends(get_admin_user)
):
    """
    Update user information (Admin only)
    """
    user = UserModel.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Build update dict
    update_fields = {}
    if update_data.role:
        update_fields["role"] = update_data.role
    if update_data.is_active is not None:
        update_fields["is_active"] = update_data.is_active
    if update_data.trial_limits:
        update_fields["trial_limits"] = update_data.trial_limits

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update fields provided"
        )

    # Update user
    success = UserModel.update_user(user_id, update_fields)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

    # Get updated user
    updated_user = UserModel.get_by_id(user_id)
    updated_user.pop("password_hash", None)

    return {
        "message": "User updated successfully",
        "user": updated_user
    }


@router.post("/users/{user_id}/add-bonus-trials")
async def add_bonus_trials(
    user_id: str,
    feature: str,
    bonus: int,
    admin_user: dict = Depends(get_admin_user)
):
    """
    Add bonus trials to a user (Admin only)
    """
    user = UserModel.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate feature
    valid_features = ["ai_designer", "virtual_tryon", "qc_inspector", "3d_generation"]
    if feature not in valid_features:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid feature. Must be one of: {', '.join(valid_features)}"
        )

    # Add bonus trials
    success = TrialUsageModel.add_bonus_trial(user_id, feature, bonus)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add bonus trials"
        )

    # Get updated user
    updated_user = UserModel.get_by_id(user_id)
    updated_user.pop("password_hash", None)

    return {
        "message": f"Added {bonus} bonus trials to {feature}",
        "user": updated_user
    }


@router.get("/activity/recent")
async def get_recent_activity(
    admin_user: dict = Depends(get_admin_user),
    limit: int = 50
):
    """
    Get recent user activity (Admin only)
    """
    db = get_mongodb()

    # Get recent trial usage
    recent_usage = list(
        db.trial_usage.find()
        .sort("timestamp", -1)
        .limit(limit)
    )

    # Enrich with user info
    for usage in recent_usage:
        usage["_id"] = str(usage["_id"])
        user = UserModel.get_by_id(usage["user_id"])
        if user:
            usage["username"] = user.get("username", "Unknown")
            usage["email"] = user.get("email", "Unknown")

    return {
        "total": len(recent_usage),
        "activity": recent_usage
    }


@router.get("/analytics/feature-usage")
async def get_feature_usage_analytics(
    admin_user: dict = Depends(get_admin_user),
    days: int = 7
):
    """
    Get feature usage analytics (Admin only)
    """
    db = get_mongodb()

    start_date = datetime.utcnow() - timedelta(days=days)

    # Aggregate usage by feature
    pipeline = [
        {
            "$match": {
                "timestamp": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": "$feature",
                "count": {"$sum": 1}
            }
        }
    ]

    feature_usage = list(db.trial_usage.aggregate(pipeline))

    # Format results
    usage_by_feature = {}
    for item in feature_usage:
        usage_by_feature[item["_id"]] = item["count"]

    return {
        "days": days,
        "start_date": start_date.isoformat(),
        "end_date": datetime.utcnow().isoformat(),
        "feature_usage": usage_by_feature
    }


@router.get("/analytics/user-growth")
async def get_user_growth_analytics(
    admin_user: dict = Depends(get_admin_user),
    days: int = 30
):
    """
    Get user growth analytics (Admin only)
    """
    db = get_mongodb()

    start_date = datetime.utcnow() - timedelta(days=days)

    # Aggregate signups by day
    pipeline = [
        {
            "$match": {
                "created_at": {"$gte": start_date}
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$created_at"
                    }
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    daily_signups = list(db.users.aggregate(pipeline))

    return {
        "days": days,
        "start_date": start_date.isoformat(),
        "end_date": datetime.utcnow().isoformat(),
        "daily_signups": daily_signups
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """
    Delete a user (Admin only) - Use with caution!
    """
    # Check if user exists
    user = UserModel.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Don't allow deleting admin users
    if user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete admin users"
        )

    db = get_mongodb()

    # Delete user
    db.users.delete_one({"_id": ObjectId(user_id)})

    # Delete related data
    db.trial_usage.delete_many({"user_id": user_id})
    db.waitlist.delete_many({"user_id": user_id})

    return {
        "message": f"User {user['username']} deleted successfully"
    }
