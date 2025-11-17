"""
AI Jewellery Designer Router
Endpoints for text-to-image jewellery generation and 3D model generation
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models.database import get_db, Design, User
from backend.models.mongodb import TrialUsageModel
from backend.services.ai_designer_service import ai_designer_service
from backend.services.s3_service import s3_service
from backend.services.model_3d_service import model_3d_service
from backend.utils.auth import get_current_verified_user
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class GenerateDesignRequest(BaseModel):
    """Request model for generating design"""
    prompt: str = Field(..., min_length=5, max_length=500, description="Design prompt")
    category: str = Field(..., description="Jewellery category: ring, necklace, earring, bracelet")
    style_preset: str = Field(..., description="Style: bridal, minimalist, traditional, antique, heavy-stone")
    realism_mode: str = Field(default="realistic", description="Realism: realistic, photoreal, cad, sketch")
    num_images: int = Field(default=4, ge=1, le=4, description="Number of images to generate")
    user_id: Optional[int] = Field(default=1, description="User ID")


class ImageData(BaseModel):
    """Image data model"""
    url: str
    revised_prompt: Optional[str] = None
    seed: str


class GenerateDesignResponse(BaseModel):
    """Response model for generated design"""
    generation_id: str
    design_id: int
    prompt: str
    enhanced_prompt: str
    category: str
    style_preset: str
    realism_mode: str
    images: List[ImageData]
    materials: List[str]
    colors: List[str]
    confidence: float
    created_at: str


class TemplatePromptsRequest(BaseModel):
    """Request for template prompts"""
    category: str
    style_preset: str


class SaveIdeaRequest(BaseModel):
    """Request to save design as idea"""
    design_id: int
    is_favorite: Optional[bool] = False


@router.post("/generate", response_model=GenerateDesignResponse)
async def generate_design(
    request: GenerateDesignRequest,
    current_user: Dict[str, Any] = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Generate jewellery design from text prompt (Requires authentication)

    This endpoint:
    1. Checks trial limits
    2. Enhances the user's prompt
    3. Generates images using DALL-E
    4. Analyzes the design with Claude
    5. Saves to database
    6. Records trial usage
    7. Returns results with URLs
    """
    try:
        user_id = current_user["_id"]

        # Check trial limit
        trial_status = TrialUsageModel.check_trial_limit(user_id, "ai_designer")
        if not trial_status["allowed"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "trial_limit_reached",
                    "message": f"You've used all {trial_status['limit']} trials for AI Designer. Join our waitlist for unlimited access!",
                    "trial_status": trial_status
                }
            )

        logger.info(f"Generating design for user {current_user['username']}: {request.category} - {request.style_preset}")

        # Generate design
        result = await ai_designer_service.generate_design(
            prompt=request.prompt,
            category=request.category,
            style_preset=request.style_preset,
            realism_mode=request.realism_mode,
            num_images=request.num_images
        )

        # Record trial usage
        TrialUsageModel.record_usage(user_id, "ai_designer")

        # Upload images to S3 (optional, for persistence)
        # For now, we'll use the DALL-E URLs directly
        # In production, you might want to download and re-upload to your S3

        # Save to database
        design = Design(
            user_id=request.user_id,
            category=request.category,
            style_preset=request.style_preset,
            prompt=request.prompt,
            realism_mode=request.realism_mode,
            generated_images=[img["url"] for img in result["images"]],
            seed_id=result["images"][0]["seed"] if result["images"] else "",
            model_version=result["model"],
            generation_id=result["generation_id"],
            dominant_materials=result["materials"],
            dominant_colors=result["colors"],
            confidence_score=result["confidence"]
        )

        db.add(design)
        db.commit()
        db.refresh(design)

        logger.info(f"Design saved: {design.id}")

        return GenerateDesignResponse(
            generation_id=result["generation_id"],
            design_id=design.id,
            prompt=request.prompt,
            enhanced_prompt=result["enhanced_prompt"],
            category=request.category,
            style_preset=request.style_preset,
            realism_mode=request.realism_mode,
            images=[ImageData(**img) for img in result["images"]],
            materials=result["materials"],
            colors=result["colors"],
            confidence=result["confidence"],
            created_at=result["created_at"]
        )

    except Exception as e:
        logger.error(f"Error generating design: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates")
async def get_template_prompts(request: TemplatePromptsRequest):
    """
    Get template prompts for a category and style

    Returns pre-defined example prompts that users can use
    """
    try:
        templates = ai_designer_service.get_template_prompts(
            request.category,
            request.style_preset
        )

        return {
            "category": request.category,
            "style_preset": request.style_preset,
            "templates": templates
        }

    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-idea")
async def save_as_idea(
    request: SaveIdeaRequest,
    db: Session = Depends(get_db)
):
    """
    Mark a design as saved idea
    """
    try:
        design = db.query(Design).filter(Design.id == request.design_id).first()

        if not design:
            raise HTTPException(status_code=404, detail="Design not found")

        design.is_idea = True
        if request.is_favorite:
            design.is_favorite = True

        db.commit()

        return {
            "success": True,
            "design_id": design.id,
            "message": "Design saved as idea"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving idea: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/designs/{design_id}")
async def get_design(design_id: int, db: Session = Depends(get_db)):
    """
    Get design by ID
    """
    try:
        design = db.query(Design).filter(Design.id == design_id).first()

        if not design:
            raise HTTPException(status_code=404, detail="Design not found")

        return {
            "id": design.id,
            "generation_id": design.generation_id,
            "category": design.category,
            "style_preset": design.style_preset,
            "prompt": design.prompt,
            "realism_mode": design.realism_mode,
            "images": design.generated_images,
            "materials": design.dominant_materials,
            "colors": design.dominant_colors,
            "confidence": design.confidence_score,
            "is_favorite": design.is_favorite,
            "is_idea": design.is_idea,
            "created_at": design.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting design: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/designs")
async def list_designs(
    user_id: int = 1,
    category: Optional[str] = None,
    style_preset: Optional[str] = None,
    is_idea: Optional[bool] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List designs with filters
    """
    try:
        query = db.query(Design).filter(Design.user_id == user_id)

        if category:
            query = query.filter(Design.category == category)
        if style_preset:
            query = query.filter(Design.style_preset == style_preset)
        if is_idea is not None:
            query = query.filter(Design.is_idea == is_idea)

        total = query.count()
        designs = query.order_by(Design.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "designs": [
                {
                    "id": d.id,
                    "generation_id": d.generation_id,
                    "category": d.category,
                    "style_preset": d.style_preset,
                    "prompt": d.prompt,
                    "thumbnail": d.generated_images[0] if d.generated_images else None,
                    "is_favorite": d.is_favorite,
                    "is_idea": d.is_idea,
                    "created_at": d.created_at.isoformat()
                }
                for d in designs
            ]
        }

    except Exception as e:
        logger.error(f"Error listing designs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/designs/{design_id}")
async def delete_design(design_id: int, db: Session = Depends(get_db)):
    """
    Delete a design
    """
    try:
        design = db.query(Design).filter(Design.id == design_id).first()

        if not design:
            raise HTTPException(status_code=404, detail="Design not found")

        db.delete(design)
        db.commit()

        return {
            "success": True,
            "message": "Design deleted"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting design: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-3d")
async def generate_3d_model(
    file: Optional[UploadFile] = File(default=None, description="2D image file (JPEG, PNG)"),
    image_url: Optional[str] = Form(default=None, description="URL of image to convert to 3D"),
    remove_background: bool = Form(default=True, description="Remove background before processing"),
    export_format: str = Form(default="glb", description="Export format: glb, obj, ply, stl"),
    current_user: Dict[str, Any] = Depends(get_current_verified_user)
):
    """
    Generate 3D model from 2D jewellery image (Requires authentication)

    This endpoint:
    1. Checks trial limits
    2. Accepts either a 2D image upload OR an image URL
    3. Optionally removes background
    4. Generates 3D mesh using TripoSR
    5. Exports to specified format (GLB, OBJ, PLY, STL)
    6. Records trial usage
    7. Returns model data as base64 data URL

    Args:
        file: Image file to convert to 3D (optional if image_url provided)
        image_url: URL of image to convert to 3D (optional if file provided)
        remove_background: Whether to remove background (default: True)
        export_format: Output format (default: glb)

    Returns:
        3D model data with metadata
    """
    try:
        user_id = current_user["_id"]

        # Check trial limit
        trial_status = TrialUsageModel.check_trial_limit(user_id, "3d_generation")
        if not trial_status["allowed"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "trial_limit_reached",
                    "message": f"You've used all {trial_status['limit']} trials for 3D Generation. Join our waitlist for unlimited access!",
                    "trial_status": trial_status
                }
            )

        logger.info(f"Generating 3D model for user {current_user['username']}")

        # Validate that at least one input method is provided
        if not file and not image_url:
            raise HTTPException(
                status_code=400,
                detail="Either 'file' or 'image_url' must be provided"
            )

        # Validate export format
        supported_formats = model_3d_service.get_supported_formats()
        if export_format not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {export_format}. Supported: {', '.join(supported_formats)}"
            )

        # Load image from file or URL
        if file:
            # Validate file type
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.content_type}. Must be an image."
                )
            logger.info(f"Generating 3D model from uploaded file: {file.filename}, format: {export_format}")
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
        else:
            # Fetch image from URL (now S3 URLs which are publicly accessible)
            logger.info(f"Generating 3D model from URL: {image_url}, format: {export_format}")
            import httpx

            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(image_url)
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to fetch image from URL: HTTP {response.status_code}"
                    )
                image = Image.open(io.BytesIO(response.content))

        # Generate 3D model
        result = await model_3d_service.generate_3d_model(
            image=image,
            remove_background=remove_background,
            export_format=export_format
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "3D generation failed")
            )

        logger.info(f"3D model generated successfully: {result['generation_id']}")

        # Record trial usage
        TrialUsageModel.record_usage(user_id, "3d_generation")

        return {
            "success": True,
            "generation_id": result["generation_id"],
            "model_url": result["model_url"],
            "thumbnail_url": result["thumbnail_url"],
            "format": result["format"],
            "mime_type": result["mime_type"],
            "file_size": result["file_size"],
            "stats": result["stats"],
            "background_removed": result["background_removed"],
            "created_at": result["created_at"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating 3D model: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate 3D model: {str(e)}"
        )


@router.get("/3d-formats")
async def get_supported_3d_formats():
    """
    Get list of supported 3D export formats

    Returns:
        List of supported format strings
    """
    return {
        "formats": model_3d_service.get_supported_formats(),
        "recommended": "glb",
        "descriptions": {
            "glb": "GL Transmission Format Binary - Best for web viewing",
            "obj": "Wavefront OBJ - Widely compatible, good for editing",
            "ply": "Polygon File Format - Good for 3D printing",
            "stl": "Stereolithography - Standard for 3D printing"
        }
    }
