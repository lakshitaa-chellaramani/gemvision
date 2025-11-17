"""
Virtual Try-On Router
Endpoints for virtual try-on functionality with AI-powered Veo 2 integration
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models.database import get_db, TryOn, Design
from backend.models.mongodb import TrialUsageModel
from backend.services.s3_service import s3_service
from backend.services.virtual_tryon_service import virtual_tryon_service
from backend.utils.auth import get_current_verified_user
from PIL import Image, ImageDraw
import io
import logging
import json
import base64

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


# ============================================================================
# AI-POWERED VIRTUAL TRY-ON ENDPOINTS (Gemini Imagen 3 - Banana)
# ============================================================================

class GenerateTryOnRequest(BaseModel):
    """Request for AI-powered virtual try-on"""
    jewelry_type: str = Field(..., description="Type: ring, bracelet, necklace, earring")
    jewelry_description: str = Field(..., description="Description of the jewelry")
    target_area: str = Field(default="ring finger", description="Placement area")
    use_examples: bool = Field(default=True, description="Use few-shot learning")
    design_id: Optional[int] = None


@router.post("/generate-ai-tryon")
async def generate_ai_tryon(
    body_photo: UploadFile = File(..., description="Photo of body part (hand, neck, full body, etc.)"),
    jewelry_photo: UploadFile = File(...),
    jewelry_type: str = Form(..., description="ring, bracelet, necklace, or earring"),
    jewelry_description: str = Form(...),
    target_area: Optional[str] = Form(None, description="Optional - will auto-detect if not provided"),
    use_examples: bool = Form(True),
    auto_detect: bool = Form(True, description="Automatically detect body part and placement"),
    design_id: Optional[int] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_verified_user)
):
    """
    Generate AI-powered virtual try-on using Gemini Imagen 3 (Banana) with AUTO-DETECTION (Requires authentication)

    This endpoint intelligently handles ANY body photo:
    - Upload a HAND photo → Places ring/bracelet automatically
    - Upload a NECK photo → Places necklace automatically
    - Upload FULL BODY → Detects appropriate area for jewelry
    - Upload EAR photo → Places earring automatically

    Features:
    1. Checks trial limits
    2. Auto-detects body part in the uploaded photo
    3. Determines best placement area for the jewelry type
    4. Uses Gemini Imagen 3 (Banana) for intelligent analysis and image generation
    5. Optionally uses example pairs for few-shot learning
    6. Generates photorealistic try-on images with AI compositing
    7. Records trial usage

    Upload example pairs to backend/assets/tryon_examples/ for better results!
    """
    try:
        user_id = current_user["_id"]

        # Check trial limit
        trial_status = TrialUsageModel.check_trial_limit(user_id, "virtual_tryon")
        if not trial_status["allowed"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "trial_limit_reached",
                    "message": f"You've used all {trial_status['limit']} trials for Virtual Try-On. Join our waitlist for unlimited access!",
                    "trial_status": trial_status
                }
            )

        logger.info(f"Generating AI try-on for user {current_user['username']}: {jewelry_type}")
        # Validate file types
        for file in [body_photo, jewelry_photo]:
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"{file.filename} must be an image")

        # Read and validate images
        body_contents = await body_photo.read()
        jewelry_contents = await jewelry_photo.read()

        try:
            body_image = Image.open(io.BytesIO(body_contents)).convert("RGB")
            jewelry_image = Image.open(io.BytesIO(jewelry_contents)).convert("RGBA")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")

        # Resize if too large (for API limits)
        max_size = 2048
        for img_name, img in [("body", body_image), ("jewelry", jewelry_image)]:
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                if img_name == "body":
                    body_image = img.resize(new_size, Image.Resampling.LANCZOS)
                else:
                    jewelry_image = img.resize(new_size, Image.Resampling.LANCZOS)

        if auto_detect:
            logger.info(f"Generating AI try-on for {jewelry_type} with AUTO-DETECTION")
        else:
            logger.info(f"Generating AI try-on for {jewelry_type} on {target_area}")

        # Generate try-on using Veo 2 with auto-detection
        result = await virtual_tryon_service.generate_tryon(
            body_image=body_image,
            jewelry_image=jewelry_image,
            jewelry_type=jewelry_type,
            jewelry_description=jewelry_description,
            target_area=target_area,
            use_examples=use_examples,
            auto_detect=auto_detect
        )

        logger.info(f"AI try-on generated successfully")

        # Record trial usage
        TrialUsageModel.record_usage(user_id, "virtual_tryon")

        # Build response
        response = {
            "success": True,
            **result,
            "design_id": design_id,
            "auto_detection_used": auto_detect and target_area is None
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating AI try-on: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CompositeTryOnRequest(BaseModel):
    """Request to composite jewelry onto hand photo"""
    placement_data: Dict = Field(..., description="Placement instructions from AI analysis")


@router.post("/composite-tryon")
async def composite_tryon(
    body_photo: UploadFile = File(..., description="Photo of any body part"),
    jewelry_photo: UploadFile = File(...),
    jewelry_type: str = Form("jewelry", description="Type of jewelry"),
    jewelry_description: str = Form("", description="Description of jewelry"),
    save_to_db: bool = Form(False),
    user_id: int = Form(1),
    design_id: Optional[int] = Form(None)
):
    """
    Generate AI-powered virtual try-on composite image using Gemini 2.5

    Works with any body part photo (hand, neck, full body, ear, etc.)
    Uses Gemini AI to create a photorealistic composite image
    """
    try:
        # Read images
        body_contents = await body_photo.read()
        jewelry_contents = await jewelry_photo.read()

        body_image = Image.open(io.BytesIO(body_contents)).convert("RGB")
        jewelry_image = Image.open(io.BytesIO(jewelry_contents)).convert("RGBA")

        logger.info("Generating AI-powered virtual try-on...")

        # Generate using AI instead of simple compositing
        result = await virtual_tryon_service.generate_tryon_image(
            person_image=body_image,
            jewelry_image=jewelry_image,
            jewelry_type=jewelry_type,
            jewelry_description=jewelry_description
        )

        # Extract the generated image from local storage
        result_image = Image.open(result["local_path"])

        logger.info(f"AI try-on generated successfully")

        response_data = {
            "success": True,
            "result_url": result["result_url"],
            "local_url": result["local_url"],
            "s3_url": result.get("s3_url"),
            "model_used": result["model_used"],
            "generation_method": result["generation_method"]
        }

        # Save to database if requested
        if save_to_db:
            from backend.models.database import SessionLocal
            db = SessionLocal()

            tryon = TryOn(
                user_id=user_id,
                design_id=design_id,
                hand_photo_url=result["local_url"],
                overlay_image_url=result["local_url"],
                overlay_transform={},  # No manual transform needed with AI generation
                finger_type=jewelry_type,
                snapshot_url=result["result_url"]
            )

            db.add(tryon)
            db.commit()
            db.refresh(tryon)
            db.close()

            response_data["tryon_id"] = tryon.id
            logger.info(f"Saved AI try-on to database: {tryon.id}")

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error compositing try-on: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples/status")
async def get_examples_status():
    """
    Check status of AI-powered virtual try-on service

    Returns information about the service configuration
    """
    try:
        return {
            "success": True,
            "model": virtual_tryon_service.model_name,
            "generation_method": "gemini_ai_image_generation",
            "message": f"AI-powered virtual try-on using {virtual_tryon_service.model_name}",
            "features": [
                "Automatic body part detection",
                "Intelligent jewelry placement",
                "Professional model-style transformations",
                "Studio-quality lighting and backgrounds",
                "Photorealistic compositing"
            ]
        }

    except Exception as e:
        logger.error(f"Error checking service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
