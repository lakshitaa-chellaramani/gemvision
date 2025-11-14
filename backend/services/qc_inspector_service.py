"""
AI Quality Inspector Service
Detects defects in jewellery images using simulated or ML-based detection
"""
import numpy as np
from PIL import Image
import io
import random
from typing import List, Dict, Tuple
import logging
from backend.app.config import settings
import uuid

logger = logging.getLogger(__name__)


class QCInspectorService:
    """Service for quality inspection of jewellery"""

    DEFECT_TYPES = [
        "scratch",
        "stone_misalignment",
        "surface_discoloration",
        "prong_damage",
        "polish_defect",
        "casting_porosity",
        "size_deviation",
        "engraving_error"
    ]

    SEVERITY_LEVELS = ["low", "medium", "high"]

    def __init__(self):
        self.mode = settings.qc_mode
        self.confidence_threshold = settings.qc_confidence_threshold

    def _generate_simulated_defects(
        self,
        image_width: int,
        image_height: int,
        num_defects: int = None
    ) -> List[Dict]:
        """
        Generate simulated defects for demo purposes

        Args:
            image_width: Image width
            image_height: Image height
            num_defects: Number of defects (random if None)

        Returns:
            List of defect dictionaries
        """
        if num_defects is None:
            # Random 0-3 defects
            num_defects = random.randint(0, 3)

        defects = []

        for _ in range(num_defects):
            # Random position
            x = random.randint(int(image_width * 0.2), int(image_width * 0.8))
            y = random.randint(int(image_height * 0.2), int(image_height * 0.8))

            # Random size (10-20% of image dimension)
            w = random.randint(int(image_width * 0.1), int(image_width * 0.2))
            h = random.randint(int(image_height * 0.1), int(image_height * 0.2))

            # Random defect type
            defect_type = random.choice(self.DEFECT_TYPES)

            # Random confidence (70-95%)
            confidence = random.uniform(0.70, 0.95)

            # Severity based on confidence
            if confidence > 0.85:
                severity = "high"
            elif confidence > 0.75:
                severity = "medium"
            else:
                severity = "low"

            defect = {
                "id": uuid.uuid4().hex[:8],
                "type": defect_type,
                "label": defect_type.replace("_", " ").title(),
                "bbox": {
                    "x": max(0, x - w // 2),
                    "y": max(0, y - h // 2),
                    "width": w,
                    "height": h
                },
                "confidence": round(confidence, 2),
                "severity": severity,
                "description": self._get_defect_description(defect_type)
            }

            defects.append(defect)

        return defects

    def _get_defect_description(self, defect_type: str) -> str:
        """Get human-readable description for defect type"""
        descriptions = {
            "scratch": "Surface scratch detected on metal finish",
            "stone_misalignment": "Stone appears misaligned or loose in setting",
            "surface_discoloration": "Discoloration or tarnish detected on surface",
            "prong_damage": "Prong appears damaged or bent",
            "polish_defect": "Inconsistent polish or surface finish",
            "casting_porosity": "Porosity or air pockets in casting",
            "size_deviation": "Dimension appears outside tolerance",
            "engraving_error": "Engraving appears incorrect or damaged"
        }
        return descriptions.get(defect_type, "Defect detected")

    def _analyze_image_characteristics(self, image: Image.Image) -> Dict:
        """
        Analyze image for basic characteristics that affect QC

        Args:
            image: PIL Image

        Returns:
            Analysis dict
        """
        # Convert to numpy array
        img_array = np.array(image)

        # Calculate brightness
        brightness = np.mean(img_array)

        # Calculate contrast
        contrast = np.std(img_array)

        # Detect if image is too dark or too bright
        lighting_quality = "good"
        if brightness < 80:
            lighting_quality = "too_dark"
        elif brightness > 200:
            lighting_quality = "too_bright"
        elif contrast < 30:
            lighting_quality = "low_contrast"

        # Detect glint (very bright spots)
        has_glint = np.max(img_array) > 245 and np.sum(img_array > 240) > (img_array.size * 0.01)

        return {
            "brightness": float(brightness),
            "contrast": float(contrast),
            "lighting_quality": lighting_quality,
            "has_glint": bool(has_glint),
            "resolution": image.size
        }

    async def inspect_image(
        self,
        image_bytes: bytes,
        force_simulated: bool = False
    ) -> Dict:
        """
        Inspect image for defects

        Args:
            image_bytes: Image data
            force_simulated: Force simulated mode

        Returns:
            Inspection result dictionary
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            width, height = image.size

            # Analyze image characteristics
            image_analysis = self._analyze_image_characteristics(image)

            # Generate inspection ID
            inspection_id = f"qc_{uuid.uuid4().hex}"

            # Check if should use simulated mode
            use_simulated = force_simulated or self.mode == "simulated"

            if use_simulated:
                # Generate simulated defects
                defects = self._generate_simulated_defects(width, height)
                detection_mode = "simulated"
            else:
                # Use ML model (placeholder for now)
                defects = await self._detect_with_ml(image)
                detection_mode = "ml"

            # Filter by confidence threshold
            defects = [d for d in defects if d["confidence"] >= self.confidence_threshold]

            # Determine overall status
            if not defects:
                status = "passed"
                recommendation = "No defects detected. Item passes QC."
            elif any(d["severity"] == "high" for d in defects):
                status = "failed"
                recommendation = "Critical defects detected. Send for rework."
            elif any(d["severity"] == "medium" for d in defects):
                status = "review"
                recommendation = "Moderate defects detected. Manual review recommended."
            else:
                status = "passed_with_notes"
                recommendation = "Minor defects detected. Acceptable but document findings."

            # Build result
            result = {
                "inspection_id": inspection_id,
                "status": status,
                "recommendation": recommendation,
                "defects": defects,
                "defect_count": len(defects),
                "detection_mode": detection_mode,
                "confidence_threshold": self.confidence_threshold,
                "image_analysis": image_analysis,
                "requires_reshoot": image_analysis["lighting_quality"] != "good",
                "lighting_warning": self._get_lighting_warning(image_analysis)
            }

            logger.info(f"Inspection {inspection_id}: {status}, {len(defects)} defects")
            return result

        except Exception as e:
            logger.error(f"Error during inspection: {e}")
            raise

    async def _detect_with_ml(self, image: Image.Image) -> List[Dict]:
        """
        Detect defects using ML model (placeholder)

        In a real implementation, this would:
        1. Load a trained model (TensorFlow, PyTorch)
        2. Preprocess the image
        3. Run inference
        4. Post-process detections

        Args:
            image: PIL Image

        Returns:
            List of detected defects
        """
        # For now, fall back to simulated
        # TODO: Implement actual ML model loading and inference
        logger.info("ML mode not yet implemented, using simulated")
        return self._generate_simulated_defects(image.width, image.height)

    def _get_lighting_warning(self, image_analysis: Dict) -> str:
        """Get warning message for lighting issues"""
        quality = image_analysis["lighting_quality"]

        warnings = {
            "too_dark": "Image is too dark. Please recapture under better lighting.",
            "too_bright": "Image is overexposed. Reduce lighting or adjust camera settings.",
            "low_contrast": "Low contrast detected. Improve lighting setup for better detection.",
            "good": ""
        }

        warning = warnings.get(quality, "")

        if image_analysis.get("has_glint"):
            warning += " Glare detected - may cause false positives."

        return warning.strip()

    def create_rework_job(
        self,
        inspection_result: Dict,
        selected_defects: List[str],
        operator_notes: str = "",
        priority: str = "medium",
        assigned_station: str = ""
    ) -> Dict:
        """
        Create a rework job from inspection results

        Args:
            inspection_result: The inspection result
            selected_defects: List of defect IDs to rework
            operator_notes: Operator's notes
            priority: Job priority
            assigned_station: Station to assign to

        Returns:
            Rework job dictionary
        """
        from datetime import datetime

        # Filter selected defects
        defects = [
            d for d in inspection_result["defects"]
            if d["id"] in selected_defects
        ]

        rework_job_id = f"rework_{uuid.uuid4().hex[:8]}"

        rework_job = {
            "id": rework_job_id,
            "inspection_id": inspection_result["inspection_id"],
            "defects": defects,
            "operator_notes": operator_notes,
            "priority": priority,
            "assigned_station": assigned_station,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "lifecycle": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "pending",
                    "action": "created",
                    "notes": "Rework job created from QC inspection"
                }
            ]
        }

        logger.info(f"Created rework job: {rework_job_id}")
        return rework_job

    def get_defect_heatmap_data(self, inspection_result: Dict) -> Dict:
        """
        Generate heatmap data for visualization

        Args:
            inspection_result: Inspection result

        Returns:
            Heatmap data
        """
        defects = inspection_result.get("defects", [])

        heatmap_points = []
        for defect in defects:
            bbox = defect["bbox"]
            center_x = bbox["x"] + bbox["width"] // 2
            center_y = bbox["y"] + bbox["height"] // 2

            heatmap_points.append({
                "x": center_x,
                "y": center_y,
                "intensity": defect["confidence"],
                "radius": max(bbox["width"], bbox["height"]) // 2
            })

        return {
            "points": heatmap_points,
            "image_size": inspection_result.get("image_analysis", {}).get("resolution", [1024, 1024])
        }


# Global service instance
qc_inspector_service = QCInspectorService()
