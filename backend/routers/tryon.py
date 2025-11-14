"""
Virtual Try-On Router
Endpoints for virtual try-on functionality
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict
from sqlalchemy.orm import Session
from backend.models.database import get_db, TryOn, Design
from backend.services.s3_service import s3_service
from PIL import Image, ImageDraw
import io
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class TransformData(BaseModel):
    """Transform data for overlay"""
    x: float
    y: float
    scale: float
    rotation: float
    opacity: float = 1.0
    hue: float = 0.0


class AnchorPoints(BaseModel):
    """Finger anchor points"""
    knuckle: Optional[Dict[str, float]] = None
    base: Optional[Dict[str, float]] = None


class SaveTryOnRequest(BaseModel):
    """Request to save try-on"""
    user_id: int = 1
    design_id: Optional[int] = None
    hand_photo_url: str
    overlay_image_url: str
    transform: TransformData
    finger_type: str
    anchor_points: Optional[AnchorPoints] = None


class SaveSnapshotRequest(BaseModel):
    """Request to save snapshot"""
    tryon_id: int
    snapshot_data: str  # Base64 encoded image


@router.post("/upload-hand-photo")
async def upload_hand_photo(
    file: UploadFile = File(...),
):
    """
    Upload hand photo for try-on

    Accepts image upload and stores in S3
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Read file
        contents = await file.read()

        # Validate size (max 10MB)
        max_size = 10 * 1024 * 1024
        if len(contents) > max_size:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        # Validate it's a valid image
        try:
            image = Image.open(io.BytesIO(contents))
            image.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Re-open for processing
        image = Image.open(io.BytesIO(contents))

        # Resize if too large (max 2048px)
        max_dimension = 2048
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Upload to S3
        url, key = s3_service.upload_from_pil(
            image,
            folder="tryon/hand-photos",
            format="JPEG"
        )

        # Create thumbnail
        thumbnail_url, thumb_key = s3_service.create_thumbnail(
            contents,
            max_size=(300, 300),
            folder="tryon/thumbnails"
        )

        logger.info(f"Uploaded hand photo: {url}")

        return {
            "success": True,
            "url": url,
            "key": key,
            "thumbnail_url": thumbnail_url,
            "dimensions": {
                "width": image.width,
                "height": image.height
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading hand photo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_tryon(
    request: SaveTryOnRequest,
    db: Session = Depends(get_db)
):
    """
    Save try-on session
    """
    try:
        # Create try-on record
        tryon = TryOn(
            user_id=request.user_id,
            design_id=request.design_id,
            hand_photo_url=request.hand_photo_url,
            overlay_image_url=request.overlay_image_url,
            overlay_transform=request.transform.dict(),
            finger_type=request.finger_type,
            anchor_points=request.anchor_points.dict() if request.anchor_points else None
        )

        db.add(tryon)
        db.commit()
        db.refresh(tryon)

        logger.info(f"Saved try-on: {tryon.id}")

        return {
            "success": True,
            "tryon_id": tryon.id,
            "message": "Try-on saved successfully"
        }

    except Exception as e:
        logger.error(f"Error saving try-on: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-snapshot")
async def save_snapshot(
    tryon_id: int = Form(...),
    snapshot_file: UploadFile = File(...)
):
    """
    Save try-on snapshot

    Takes the final composed image and saves it
    """
    try:
        # Read snapshot
        contents = await snapshot_file.read()

        # Upload to S3
        url, key = s3_service.upload_image(
            contents,
            folder="tryon/snapshots",
            content_type=snapshot_file.content_type or "image/png"
        )

        # Update try-on record
        from backend.models.database import SessionLocal
        db = SessionLocal()

        tryon = db.query(TryOn).filter(TryOn.id == tryon_id).first()

        if not tryon:
            raise HTTPException(status_code=404, detail="Try-on not found")

        tryon.snapshot_url = url
        tryon.snapshot_filename = key.split('/')[-1]

        db.commit()
        db.close()

        logger.info(f"Saved snapshot for try-on: {tryon_id}")

        return {
            "success": True,
            "snapshot_url": url,
            "message": "Snapshot saved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-for-approval")
async def send_for_approval(
    tryon_id: int,
    recipient_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Send try-on for approval

    Marks try-on as sent for approval and optionally sends email
    """
    try:
        tryon = db.query(TryOn).filter(TryOn.id == tryon_id).first()

        if not tryon:
            raise HTTPException(status_code=404, detail="Try-on not found")

        tryon.sent_for_approval = True
        db.commit()

        # Generate shareable link
        share_url = f"{settings.backend_url}/api/tryon/view/{tryon_id}"

        # TODO: Send email if recipient_email provided
        # This would use an email service like SendGrid, AWS SES, etc.

        logger.info(f"Try-on {tryon_id} sent for approval")

        return {
            "success": True,
            "share_url": share_url,
            "message": "Try-on sent for approval"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending for approval: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/view/{tryon_id}")
async def view_tryon(tryon_id: int, db: Session = Depends(get_db)):
    """
    View try-on by ID (for shareable links)
    """
    try:
        tryon = db.query(TryOn).filter(TryOn.id == tryon_id).first()

        if not tryon:
            raise HTTPException(status_code=404, detail="Try-on not found")

        # Get associated design if exists
        design_info = None
        if tryon.design_id:
            design = db.query(Design).filter(Design.id == tryon.design_id).first()
            if design:
                design_info = {
                    "id": design.id,
                    "category": design.category,
                    "style_preset": design.style_preset,
                    "prompt": design.prompt
                }

        return {
            "id": tryon.id,
            "hand_photo_url": tryon.hand_photo_url,
            "overlay_image_url": tryon.overlay_image_url,
            "snapshot_url": tryon.snapshot_url,
            "transform": tryon.overlay_transform,
            "finger_type": tryon.finger_type,
            "design": design_info,
            "is_approved": tryon.is_approved,
            "created_at": tryon.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing try-on: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_tryons(
    user_id: int = 1,
    design_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List try-on sessions
    """
    try:
        query = db.query(TryOn).filter(TryOn.user_id == user_id)

        if design_id:
            query = query.filter(TryOn.design_id == design_id)

        total = query.count()
        tryons = query.order_by(TryOn.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "tryons": [
                {
                    "id": t.id,
                    "design_id": t.design_id,
                    "snapshot_url": t.snapshot_url,
                    "finger_type": t.finger_type,
                    "is_approved": t.is_approved,
                    "sent_for_approval": t.sent_for_approval,
                    "created_at": t.created_at.isoformat()
                }
                for t in tryons
            ]
        }

    except Exception as e:
        logger.error(f"Error listing try-ons: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tryon_id}")
async def delete_tryon(tryon_id: int, db: Session = Depends(get_db)):
    """
    Delete try-on
    """
    try:
        tryon = db.query(TryOn).filter(TryOn.id == tryon_id).first()

        if not tryon:
            raise HTTPException(status_code=404, detail="Try-on not found")

        # Optionally delete from S3
        # s3_service.delete_image(key)

        db.delete(tryon)
        db.commit()

        return {
            "success": True,
            "message": "Try-on deleted"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting try-on: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Import settings
from backend.app.config import settings
