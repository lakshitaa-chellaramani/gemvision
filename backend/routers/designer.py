"""
AI Jewellery Designer Router
Endpoints for text-to-image jewellery generation
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models.database import get_db, Design, User
from backend.services.ai_designer_service import ai_designer_service
from backend.services.s3_service import s3_service
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
    db: Session = Depends(get_db)
):
    """
    Generate jewellery design from text prompt

    This endpoint:
    1. Enhances the user's prompt
    2. Generates images using DALL-E
    3. Analyzes the design with Claude
    4. Saves to database
    5. Returns results with URLs
    """
    try:
        logger.info(f"Generating design: {request.category} - {request.style_preset}")

        # Generate design
        result = await ai_designer_service.generate_design(
            prompt=request.prompt,
            category=request.category,
            style_preset=request.style_preset,
            realism_mode=request.realism_mode,
            num_images=request.num_images
        )

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
