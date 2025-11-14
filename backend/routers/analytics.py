"""
Analytics Router
Endpoints for tracking and analytics
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.models.database import get_db, Analytics, Design, TryOn, QCInspection
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class LogEventRequest(BaseModel):
    """Request to log analytics event"""
    event_type: str = Field(..., description="generation, tryon, qc, etc.")
    event_action: str = Field(..., description="created, viewed, approved, etc.")
    event_data: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    user_id: Optional[int] = None


@router.post("/log")
async def log_event(
    request: LogEventRequest,
    db: Session = Depends(get_db)
):
    """
    Log analytics event
    """
    try:
        event = Analytics(
            user_id=request.user_id,
            event_type=request.event_type,
            event_action=request.event_action,
            event_data=request.event_data,
            session_id=request.session_id
        )

        db.add(event)
        db.commit()

        return {
            "success": True,
            "message": "Event logged"
        }

    except Exception as e:
        logger.error(f"Error logging event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_stats(
    days: int = 30,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Total designs generated
        design_query = db.query(func.count(Design.id))
        if user_id:
            design_query = design_query.filter(Design.user_id == user_id)
        total_designs = design_query.filter(Design.created_at >= cutoff_date).scalar()

        # Total try-ons
        tryon_query = db.query(func.count(TryOn.id))
        if user_id:
            tryon_query = tryon_query.filter(TryOn.user_id == user_id)
        total_tryons = tryon_query.filter(TryOn.created_at >= cutoff_date).scalar()

        # Total QC inspections
        qc_query = db.query(func.count(QCInspection.id))
        if user_id:
            qc_query = qc_query.filter(QCInspection.user_id == user_id)
        total_inspections = qc_query.filter(QCInspection.created_at >= cutoff_date).scalar()

        # Designs by category
        designs_by_category = db.query(
            Design.category,
            func.count(Design.id).label('count')
        ).filter(Design.created_at >= cutoff_date)

        if user_id:
            designs_by_category = designs_by_category.filter(Design.user_id == user_id)

        designs_by_category = designs_by_category.group_by(Design.category).all()

        # Designs by style
        designs_by_style = db.query(
            Design.style_preset,
            func.count(Design.id).label('count')
        ).filter(Design.created_at >= cutoff_date)

        if user_id:
            designs_by_style = designs_by_style.filter(Design.user_id == user_id)

        designs_by_style = designs_by_style.group_by(Design.style_preset).all()

        # QC pass rate
        qc_decisions = db.query(
            QCInspection.operator_decision,
            func.count(QCInspection.id).label('count')
        ).filter(QCInspection.created_at >= cutoff_date)

        if user_id:
            qc_decisions = qc_decisions.filter(QCInspection.user_id == user_id)

        qc_decisions = qc_decisions.filter(
            QCInspection.operator_decision.isnot(None)
        ).group_by(QCInspection.operator_decision).all()

        # Try-on approval rate
        tryons_approved = db.query(func.count(TryOn.id)).filter(
            TryOn.created_at >= cutoff_date,
            TryOn.is_approved == True
        )
        if user_id:
            tryons_approved = tryons_approved.filter(TryOn.user_id == user_id)
        tryons_approved = tryons_approved.scalar()

        approval_rate = (tryons_approved / total_tryons * 100) if total_tryons > 0 else 0

        # Recent activity
        recent_designs = db.query(Design).order_by(
            desc(Design.created_at)
        ).limit(5).all()

        return {
            "period_days": days,
            "totals": {
                "designs": total_designs,
                "tryons": total_tryons,
                "inspections": total_inspections
            },
            "designs_by_category": {
                cat: count for cat, count in designs_by_category
            },
            "designs_by_style": {
                style: count for style, count in designs_by_style
            },
            "qc_decisions": {
                decision: count for decision, count in qc_decisions
            },
            "tryon_approval_rate": round(approval_rate, 2),
            "recent_activity": [
                {
                    "id": d.id,
                    "category": d.category,
                    "style_preset": d.style_preset,
                    "thumbnail": d.generated_images[0] if d.generated_images else None,
                    "created_at": d.created_at.isoformat()
                }
                for d in recent_designs
            ]
        }

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_trends(
    days: int = 30,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get trend data over time
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Daily design counts
        daily_designs = db.query(
            func.date(Design.created_at).label('date'),
            func.count(Design.id).label('count')
        ).filter(Design.created_at >= cutoff_date)

        if user_id:
            daily_designs = daily_designs.filter(Design.user_id == user_id)

        daily_designs = daily_designs.group_by(
            func.date(Design.created_at)
        ).order_by('date').all()

        # Daily try-on counts
        daily_tryons = db.query(
            func.date(TryOn.created_at).label('date'),
            func.count(TryOn.id).label('count')
        ).filter(TryOn.created_at >= cutoff_date)

        if user_id:
            daily_tryons = daily_tryons.filter(TryOn.user_id == user_id)

        daily_tryons = daily_tryons.group_by(
            func.date(TryOn.created_at)
        ).order_by('date').all()

        # Daily QC counts
        daily_qc = db.query(
            func.date(QCInspection.created_at).label('date'),
            func.count(QCInspection.id).label('count')
        ).filter(QCInspection.created_at >= cutoff_date)

        if user_id:
            daily_qc = daily_qc.filter(QCInspection.user_id == user_id)

        daily_qc = daily_qc.group_by(
            func.date(QCInspection.created_at)
        ).order_by('date').all()

        return {
            "period_days": days,
            "daily_designs": [
                {"date": str(date), "count": count}
                for date, count in daily_designs
            ],
            "daily_tryons": [
                {"date": str(date), "count": count}
                for date, count in daily_tryons
            ],
            "daily_qc": [
                {"date": str(date), "count": count}
                for date, count in daily_qc
            ]
        }

    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kpis")
async def get_kpis(
    days: int = 30,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get key performance indicators
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Average designs per day
        total_designs = db.query(func.count(Design.id)).filter(
            Design.created_at >= cutoff_date
        )
        if user_id:
            total_designs = total_designs.filter(Design.user_id == user_id)
        total_designs = total_designs.scalar()
        avg_designs_per_day = total_designs / days

        # Conversion to try-on rate
        designs_with_tryon = db.query(func.count(func.distinct(TryOn.design_id))).filter(
            TryOn.created_at >= cutoff_date,
            TryOn.design_id.isnot(None)
        )
        if user_id:
            designs_with_tryon = designs_with_tryon.filter(TryOn.user_id == user_id)
        designs_with_tryon = designs_with_tryon.scalar()

        conversion_to_tryon = (designs_with_tryon / total_designs * 100) if total_designs > 0 else 0

        # QC false positive rate
        total_qc = db.query(func.count(QCInspection.id)).filter(
            QCInspection.created_at >= cutoff_date,
            QCInspection.operator_decision.isnot(None)
        )
        if user_id:
            total_qc = total_qc.filter(QCInspection.user_id == user_id)
        total_qc = total_qc.scalar()

        false_positives = db.query(func.count(QCInspection.id)).filter(
            QCInspection.created_at >= cutoff_date,
            QCInspection.is_false_positive == True
        )
        if user_id:
            false_positives = false_positives.filter(QCInspection.user_id == user_id)
        false_positives = false_positives.scalar()

        false_positive_rate = (false_positives / total_qc * 100) if total_qc > 0 else 0

        # Average confidence score
        avg_confidence = db.query(
            func.avg(Design.confidence_score)
        ).filter(Design.created_at >= cutoff_date)
        if user_id:
            avg_confidence = avg_confidence.filter(Design.user_id == user_id)
        avg_confidence = avg_confidence.scalar() or 0

        return {
            "period_days": days,
            "avg_designs_per_day": round(avg_designs_per_day, 2),
            "conversion_to_tryon_rate": round(conversion_to_tryon, 2),
            "qc_false_positive_rate": round(false_positive_rate, 2),
            "avg_ai_confidence": round(avg_confidence, 2)
        }

    except Exception as e:
        logger.error(f"Error getting KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
