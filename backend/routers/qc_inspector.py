"""
QC Inspector Router
Endpoints for quality control inspection
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.models.database import get_db, QCInspection, ReworkJob
from backend.models.mongodb import TrialUsageModel
from backend.services.qc_inspector_service import qc_inspector_service
from backend.services.s3_service import s3_service
from backend.utils.auth import get_current_verified_user
from PIL import Image
import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response models
class InspectionRequest(BaseModel):
    """Request for inspection"""
    user_id: int = 1
    item_reference: Optional[str] = None
    force_simulated: bool = False


class TriageRequest(BaseModel):
    """Request for triaging inspection"""
    inspection_id: int
    decision: str = Field(..., description="accept, rework, or escalate")
    operator_notes: Optional[str] = ""
    is_false_positive: bool = False
    selected_defects: Optional[List[str]] = None  # Defect IDs to rework


class CreateReworkRequest(BaseModel):
    """Request to create rework job"""
    inspection_id: int
    selected_defects: List[str]
    operator_notes: str = ""
    priority: str = "medium"
    assigned_station: str = ""


class UpdateReworkRequest(BaseModel):
    """Request to update rework job status"""
    status: str = Field(..., description="pending, in_progress, completed, verified")
    operator: str = ""
    notes: str = ""


@router.post("/inspect")
async def inspect_item(
    file: UploadFile = File(...),
    item_reference: Optional[str] = Form(None),
    has_cad_file: bool = Form(True),
    force_simulated: bool = Form(False),
    current_user: Dict[str, Any] = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Inspect jewellery item for defects (Requires authentication)

    Accepts CAD files (.stl, .step, .obj), images, or PDFs for QC inspection
    """
    try:
        user_id = current_user["_id"]

        # Check trial limit
        trial_status = TrialUsageModel.check_trial_limit(user_id, "qc_inspector")
        if not trial_status["allowed"]:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "trial_limit_reached",
                    "message": f"You've used all {trial_status['limit']} trials for QC Inspector. Join our waitlist for unlimited access!",
                    "trial_status": trial_status
                }
            )

        # Log incoming request
        logger.info(f"QC Inspect request for user {current_user['username']} - Filename: {file.filename}, Content-Type: {file.content_type}")

        # Read file content first
        contents = await file.read()

        logger.info(f"File read successfully - Size: {len(contents)} bytes")

        # Validate size (check with maximum size first)
        max_size = 50 * 1024 * 1024  # 50MB max for all files
        if len(contents) > max_size:
            raise HTTPException(status_code=400, detail=f"File too large (max 50MB)")

        # Determine file type
        file_extension = file.filename.split('.')[-1].lower() if file.filename and '.' in file.filename else ''
        content_type = file.content_type or ''

        logger.info(f"File type detection - Extension: '{file_extension}', Content-Type: '{content_type}'")

        # Accepted file types
        cad_extensions = ['stl', 'step', 'stp', 'obj', 'iges', 'igs']
        image_extensions = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp', 'gif']
        pdf_extensions = ['pdf']

        is_cad = file_extension in cad_extensions
        is_image = file_extension in image_extensions or content_type.startswith("image/")
        is_pdf = file_extension in pdf_extensions or content_type == "application/pdf"

        # Try to detect as image by actually opening it if not already detected
        if not (is_cad or is_image or is_pdf):
            try:
                test_image = Image.open(io.BytesIO(contents))
                test_image.verify()
                is_image = True
                logger.info(f"Detected as image file through content analysis")
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type. Accepted: CAD files (.stl, .step, .obj), images (.jpg, .png), PDF. Filename: {file.filename}, Content-Type: {content_type}"
                )

        # For image files, validate image
        if is_image:
            try:
                test_image = Image.open(io.BytesIO(contents))
                test_image.verify()
                logger.info(f"Image validation passed")
            except Exception as e:
                logger.error(f"Image validation failed: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

        # Convert to base64 data URL for immediate display (no S3 upload needed for preview)
        import base64

        if is_image:
            # For images, create base64 data URL
            base64_data = base64.b64encode(contents).decode('utf-8')
            url = f"data:{file.content_type};base64,{base64_data}"

            # Create thumbnail
            try:
                # Re-open image from contents (don't reuse test_image after verify())
                image = Image.open(io.BytesIO(contents))
                image.thumbnail((300, 300), Image.Resampling.LANCZOS)
                thumb_buffer = io.BytesIO()
                image.save(thumb_buffer, format='PNG')
                thumb_buffer.seek(0)
                thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode('utf-8')
                thumbnail_url = f"data:image/png;base64,{thumb_base64}"
            except Exception as e:
                logger.warning(f"Failed to create thumbnail: {e}")
                thumbnail_url = url
        else:
            # For CAD/PDF files, still need a placeholder or we could upload to S3 if needed
            # For now, just use a data URL
            base64_data = base64.b64encode(contents).decode('utf-8')
            content_type = file.content_type or 'application/octet-stream'
            url = f"data:{content_type};base64,{base64_data}"
            thumbnail_url = None

        # Determine file type for inspection
        file_type = 'cad' if is_cad else 'pdf' if is_pdf else 'image'

        # Perform inspection
        inspection_result = await qc_inspector_service.inspect_file(
            contents,
            file_type=file_type,
            has_cad_file=has_cad_file,
            force_simulated=force_simulated
        )

        # Save to database
        inspection = QCInspection(
            user_id=user_id,
            item_image_url=url,
            item_thumbnail_url=thumbnail_url,
            item_reference=item_reference,
            detections=inspection_result["defects"],
            detection_mode=inspection_result["detection_mode"],
            model_version="v1.0",
            confidence_threshold=inspection_result["confidence_threshold"],
            inspected_at=datetime.utcnow()
        )

        db.add(inspection)
        db.commit()
        db.refresh(inspection)

        # Record trial usage
        TrialUsageModel.record_usage(user_id, "qc_inspector")

        logger.info(f"Inspection completed: {inspection.id} - {inspection_result['status']}")

        return {
            "inspection_id": inspection.id,
            "status": inspection_result["status"],
            "recommendation": inspection_result["recommendation"],
            "defects": inspection_result["defects"],
            "defect_count": inspection_result["defect_count"],
            "image_url": url,
            "thumbnail_url": thumbnail_url,
            "detection_mode": inspection_result["detection_mode"],
            "file_type": inspection_result["file_type"],
            "has_cad_file": has_cad_file,
            "confidence_note": inspection_result["confidence_note"],
            "confidence_threshold": inspection_result["confidence_threshold"],
            "image_analysis": inspection_result["image_analysis"],
            "requires_reshoot": inspection_result["requires_reshoot"],
            "lighting_warning": inspection_result["lighting_warning"],
            "created_at": inspection.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during inspection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/triage")
async def triage_inspection(
    request: TriageRequest,
    db: Session = Depends(get_db)
):
    """
    Triage inspection results

    Operator decides to accept, rework, or escalate
    """
    try:
        inspection = db.query(QCInspection).filter(
            QCInspection.id == request.inspection_id
        ).first()

        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")

        # Update inspection
        inspection.operator_decision = request.decision
        inspection.operator_notes = request.operator_notes
        inspection.is_false_positive = request.is_false_positive

        # If decision is rework, create rework job
        rework_job_id = None
        if request.decision == "rework" and request.selected_defects:
            # Create rework job
            rework_job = qc_inspector_service.create_rework_job(
                inspection_result={
                    "inspection_id": f"qc_{inspection.id}",
                    "defects": inspection.detections
                },
                selected_defects=request.selected_defects,
                operator_notes=request.operator_notes,
                priority="medium"
            )

            # Save rework job to database
            rework_db = ReworkJob(
                defect_type=", ".join(set(d["type"] for d in rework_job["defects"])),
                defect_severity=max(
                    (d["severity"] for d in rework_job["defects"]),
                    key=lambda x: {"low": 1, "medium": 2, "high": 3}.get(x, 0)
                ),
                defect_description=request.operator_notes,
                evidence_images=[inspection.item_image_url],
                assigned_to_station=rework_job["assigned_station"],
                priority=rework_job["priority"],
                status="pending",
                lifecycle_events=rework_job["lifecycle"]
            )

            db.add(rework_db)
            db.commit()
            db.refresh(rework_db)

            inspection.rework_job_id = rework_db.id
            rework_job_id = rework_db.id

        db.commit()

        logger.info(f"Inspection {inspection.id} triaged: {request.decision}")

        return {
            "success": True,
            "inspection_id": inspection.id,
            "decision": request.decision,
            "rework_job_id": rework_job_id,
            "message": f"Inspection triaged: {request.decision}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triaging inspection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rework")
async def create_rework_job(
    request: CreateReworkRequest,
    db: Session = Depends(get_db)
):
    """
    Create rework job from inspection
    """
    try:
        inspection = db.query(QCInspection).filter(
            QCInspection.id == request.inspection_id
        ).first()

        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")

        # Create rework job
        rework_job = qc_inspector_service.create_rework_job(
            inspection_result={
                "inspection_id": f"qc_{inspection.id}",
                "defects": inspection.detections
            },
            selected_defects=request.selected_defects,
            operator_notes=request.operator_notes,
            priority=request.priority,
            assigned_station=request.assigned_station
        )

        # Save to database
        rework_db = ReworkJob(
            defect_type=", ".join(set(d["type"] for d in rework_job["defects"])),
            defect_severity=max(
                (d["severity"] for d in rework_job["defects"]),
                key=lambda x: {"low": 1, "medium": 2, "high": 3}.get(x, 0)
            ),
            defect_description=request.operator_notes,
            evidence_images=[inspection.item_image_url],
            assigned_to_station=request.assigned_station,
            priority=request.priority,
            status="pending",
            lifecycle_events=rework_job["lifecycle"]
        )

        db.add(rework_db)
        db.commit()
        db.refresh(rework_db)

        inspection.rework_job_id = rework_db.id
        db.commit()

        logger.info(f"Created rework job: {rework_db.id}")

        return {
            "success": True,
            "rework_job_id": rework_db.id,
            "inspection_id": inspection.id,
            "message": "Rework job created"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating rework job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/rework/{rework_job_id}")
async def update_rework_job(
    rework_job_id: int,
    request: UpdateReworkRequest,
    db: Session = Depends(get_db)
):
    """
    Update rework job status
    """
    try:
        rework = db.query(ReworkJob).filter(ReworkJob.id == rework_job_id).first()

        if not rework:
            raise HTTPException(status_code=404, detail="Rework job not found")

        # Update status
        old_status = rework.status
        rework.status = request.status

        # Update timestamps
        if request.status == "in_progress" and not rework.assigned_at:
            rework.assigned_at = datetime.utcnow()
            rework.assigned_operator = request.operator
        elif request.status == "completed" and not rework.completed_at:
            rework.completed_at = datetime.utcnow()
        elif request.status == "verified" and not rework.verified_at:
            rework.verified_at = datetime.utcnow()
            rework.verified_by = request.operator

        # Add lifecycle event
        lifecycle = rework.lifecycle_events or []
        lifecycle.append({
            "timestamp": datetime.utcnow().isoformat(),
            "status": request.status,
            "operator": request.operator,
            "action": f"Status changed from {old_status} to {request.status}",
            "notes": request.notes
        })
        rework.lifecycle_events = lifecycle

        db.commit()

        logger.info(f"Rework job {rework_job_id} updated: {request.status}")

        return {
            "success": True,
            "rework_job_id": rework_job_id,
            "status": request.status,
            "message": "Rework job updated"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating rework job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inspections/{inspection_id}")
async def get_inspection(inspection_id: int, db: Session = Depends(get_db)):
    """
    Get inspection by ID
    """
    try:
        inspection = db.query(QCInspection).filter(
            QCInspection.id == inspection_id
        ).first()

        if not inspection:
            raise HTTPException(status_code=404, detail="Inspection not found")

        # Get heatmap data
        heatmap = qc_inspector_service.get_defect_heatmap_data({
            "defects": inspection.detections,
            "image_analysis": {"resolution": [1024, 1024]}
        })

        return {
            "id": inspection.id,
            "item_reference": inspection.item_reference,
            "image_url": inspection.item_image_url,
            "thumbnail_url": inspection.item_thumbnail_url,
            "defects": inspection.detections,
            "defect_count": len(inspection.detections) if inspection.detections else 0,
            "detection_mode": inspection.detection_mode,
            "operator_decision": inspection.operator_decision,
            "operator_notes": inspection.operator_notes,
            "is_false_positive": inspection.is_false_positive,
            "rework_job_id": inspection.rework_job_id,
            "heatmap": heatmap,
            "created_at": inspection.created_at.isoformat(),
            "inspected_at": inspection.inspected_at.isoformat() if inspection.inspected_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inspection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inspections")
async def list_inspections(
    user_id: int = 1,
    decision: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List inspections
    """
    try:
        query = db.query(QCInspection).filter(QCInspection.user_id == user_id)

        if decision:
            query = query.filter(QCInspection.operator_decision == decision)

        total = query.count()
        inspections = query.order_by(
            QCInspection.created_at.desc()
        ).offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "inspections": [
                {
                    "id": i.id,
                    "item_reference": i.item_reference,
                    "thumbnail_url": i.item_thumbnail_url,
                    "defect_count": len(i.detections) if i.detections else 0,
                    "operator_decision": i.operator_decision,
                    "rework_job_id": i.rework_job_id,
                    "created_at": i.created_at.isoformat()
                }
                for i in inspections
            ]
        }

    except Exception as e:
        logger.error(f"Error listing inspections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rework/{rework_job_id}")
async def get_rework_job(rework_job_id: int, db: Session = Depends(get_db)):
    """
    Get rework job by ID
    """
    try:
        rework = db.query(ReworkJob).filter(ReworkJob.id == rework_job_id).first()

        if not rework:
            raise HTTPException(status_code=404, detail="Rework job not found")

        return {
            "id": rework.id,
            "defect_type": rework.defect_type,
            "defect_severity": rework.defect_severity,
            "defect_description": rework.defect_description,
            "evidence_images": rework.evidence_images,
            "assigned_to_station": rework.assigned_to_station,
            "assigned_operator": rework.assigned_operator,
            "priority": rework.priority,
            "status": rework.status,
            "lifecycle_events": rework.lifecycle_events,
            "created_at": rework.created_at.isoformat(),
            "assigned_at": rework.assigned_at.isoformat() if rework.assigned_at else None,
            "completed_at": rework.completed_at.isoformat() if rework.completed_at else None,
            "verified_at": rework.verified_at.isoformat() if rework.verified_at else None,
            "verified_by": rework.verified_by
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rework job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rework")
async def list_rework_jobs(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List rework jobs
    """
    try:
        query = db.query(ReworkJob)

        if status:
            query = query.filter(ReworkJob.status == status)
        if priority:
            query = query.filter(ReworkJob.priority == priority)

        total = query.count()
        reworks = query.order_by(ReworkJob.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "rework_jobs": [
                {
                    "id": r.id,
                    "defect_type": r.defect_type,
                    "defect_severity": r.defect_severity,
                    "priority": r.priority,
                    "status": r.status,
                    "assigned_to_station": r.assigned_to_station,
                    "assigned_operator": r.assigned_operator,
                    "created_at": r.created_at.isoformat()
                }
                for r in reworks
            ]
        }

    except Exception as e:
        logger.error(f"Error listing rework jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
