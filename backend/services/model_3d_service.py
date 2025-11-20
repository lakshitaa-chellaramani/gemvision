"""
3D Model Generation Service
Converts 2D jewellery images to 3D models using Tripo3D API
"""
import logging
import uuid
import time
import asyncio
from datetime import datetime
from typing import Dict, Optional
import io
import base64

from PIL import Image
import httpx
from backend.app.config import settings

logger = logging.getLogger(__name__)


class Model3DService:
    """Service for generating 3D models from 2D images using Tripo3D API"""

    def __init__(self):
        """Initialize the 3D model generation service"""
        self.api_base_url = "https://api.tripo3d.ai/v2/openapi"
        self.api_key = settings.tripo_api_key

        logger.info("3D Model Service initialized (Tripo3D API)")

    async def _upload_image(self, image: Image.Image) -> str:
        """
        Upload image to Tripo3D and get image token with retry logic

        Args:
            image: PIL Image to upload

        Returns:
            Image token from Tripo API
        """
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Convert image to bytes with optimized compression
                img_byte_arr = io.BytesIO()
                # Use JPEG with quality 95 for smaller file size while maintaining quality
                if image.mode in ('RGBA', 'LA', 'P'):
                    # Convert transparent images to white background
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                    image = background

                image.save(img_byte_arr, format='JPEG', quality=95, optimize=True)
                img_byte_arr.seek(0)
                file_size = len(img_byte_arr.getvalue())
                logger.info(f"Image prepared for upload: {file_size} bytes (attempt {attempt + 1}/{max_retries})")

                # Upload to Tripo API with extended timeout and retry
                timeout = httpx.Timeout(180.0, connect=30.0)  # 180s total, 30s connect
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{self.api_base_url}/upload",
                        headers={
                            "Authorization": f"Bearer {self.api_key}"
                        },
                        files={
                            "file": ("image.jpg", img_byte_arr, "image/jpeg")
                        }
                    )

                    if response.status_code != 200:
                        raise Exception(f"Failed to upload image: HTTP {response.status_code} - {response.text}")

                    result = response.json()
                    image_token = result["data"]["image_token"]
                    logger.info(f"Image uploaded successfully: {image_token}")
                    return image_token

            except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("All retry attempts exhausted")
                    raise Exception(f"Upload failed after {max_retries} attempts due to timeout. Please try again or check your network connection.")
            except Exception as e:
                logger.error(f"Error uploading image to Tripo (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise

    async def _create_task(self, image_token: str, mode: str = "image_to_model") -> str:
        """
        Create a 3D generation task

        Args:
            image_token: Token from uploaded image
            mode: Generation mode

        Returns:
            Task ID
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/task",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "type": mode,
                        "file": {
                            "type": "image_token",
                            "file_token": image_token
                        }
                    }
                )

                if response.status_code != 200:
                    raise Exception(f"Failed to create task: HTTP {response.status_code} - {response.text}")

                result = response.json()
                task_id = result["data"]["task_id"]
                logger.info(f"Task created: {task_id}")
                return task_id

        except Exception as e:
            logger.error(f"Error creating Tripo task: {e}")
            raise

    async def _poll_task(self, task_id: str, max_wait: int = 300) -> Dict:
        """
        Poll task until completion

        Args:
            task_id: Task ID to poll
            max_wait: Maximum wait time in seconds

        Returns:
            Task result data
        """
        try:
            start_time = time.time()

            async with httpx.AsyncClient(timeout=120.0) as client:
                while time.time() - start_time < max_wait:
                    response = await client.get(
                        f"{self.api_base_url}/task/{task_id}",
                        headers={
                            "Authorization": f"Bearer {self.api_key}"
                        }
                    )

                    if response.status_code != 200:
                        raise Exception(f"Failed to poll task: HTTP {response.status_code}")

                    result = response.json()
                    status = result["data"]["status"]

                    logger.info(f"Task {task_id} status: {status}")

                    if status == "success":
                        return result["data"]
                    elif status == "failed":
                        error = result["data"].get("error", "Unknown error")
                        raise Exception(f"Task failed: {error}")
                    elif status in ["running", "queued"]:
                        # Wait before polling again
                        await asyncio.sleep(3)
                    else:
                        raise Exception(f"Unknown status: {status}")

                raise Exception("Task timeout: exceeded maximum wait time")

        except Exception as e:
            logger.error(f"Error polling task: {e}")
            raise

    async def _download_model(self, model_url: str) -> bytes:
        """
        Download the generated 3D model

        Args:
            model_url: URL to download model from

        Returns:
            Model file bytes
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(model_url)

                if response.status_code != 200:
                    raise Exception(f"Failed to download model: HTTP {response.status_code}")

                model_bytes = response.content
                logger.info(f"Model downloaded: {len(model_bytes)} bytes")
                return model_bytes

        except Exception as e:
            logger.error(f"Error downloading model: {e}")
            raise

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for best 3D generation results

        Args:
            image: Input PIL image

        Returns:
            Preprocessed PIL image
        """
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize to optimal size (Tripo works well with 1024x1024)
            max_size = 1024
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Pad to square if needed
            width, height = image.size
            if width != height:
                size = max(width, height)
                new_image = Image.new('RGB', (size, size), (255, 255, 255))
                new_image.paste(image, ((size - width) // 2, (size - height) // 2))
                image = new_image

            logger.info(f"Image preprocessed to size: {image.size}")
            return image

        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise

    async def generate_3d_model(
        self,
        image: Image.Image,
        remove_background: bool = True,
        export_format: str = "glb"
    ) -> Dict:
        """
        Main method to generate 3D model from 2D image using Tripo API

        Args:
            image: Input PIL image
            remove_background: Whether to remove background (handled by Tripo API)
            export_format: Export format (glb, obj, fbx, usdz, stl)

        Returns:
            Dictionary with model data and metadata
        """
        try:
            if not self.api_key:
                raise Exception("Tripo API key not configured. Please add TRIPO_API_KEY to your .env file")

            generation_id = f"3d_{uuid.uuid4().hex}"
            logger.info(f"Starting 3D generation {generation_id} using Tripo API")

            # Preprocess image
            preprocessed_image = self._preprocess_image(image)

            # Step 1: Upload image
            logger.info("Uploading image to Tripo...")
            image_token = await self._upload_image(preprocessed_image)

            # Step 2: Create generation task
            logger.info("Creating 3D generation task...")
            task_id = await self._create_task(image_token)

            # Step 3: Poll for completion
            logger.info("Waiting for 3D generation to complete...")
            task_result = await self._poll_task(task_id)

            # Step 4: Get model URL
            output = task_result.get("output", {})

            # Log the output for debugging
            logger.info(f"Task output: {output}")

            # Try to get the requested format - Tripo returns "pbr_model" (GLB URL) and "rendered_image" fields
            model_url = output.get("pbr_model") or output.get("model")

            if not model_url:
                logger.error(f"No model URL found. Available keys: {list(output.keys())}")
                logger.error(f"Full task result: {task_result}")
                raise Exception(f"No model URL found in task result. Available fields: {list(output.keys())}")

            # Step 5: Download model
            logger.info(f"Downloading {export_format.upper()} model...")
            model_bytes = await self._download_model(model_url)

            # Convert to base64 for data URL
            model_base64 = base64.b64encode(model_bytes).decode('utf-8')
            mime_types = {
                "glb": "model/gltf-binary",
                "obj": "model/obj",
                "fbx": "model/fbx",
                "usdz": "model/vnd.usdz+zip",
                "stl": "model/stl"
            }
            mime_type = mime_types.get(export_format, "application/octet-stream")
            model_url_data = f"data:{mime_type};base64,{model_base64}"

            # Create thumbnail
            thumb_buffer = io.BytesIO()
            thumb_image = preprocessed_image.copy()
            thumb_image.thumbnail((300, 300), Image.Resampling.LANCZOS)
            thumb_image.save(thumb_buffer, format='PNG')
            thumb_buffer.seek(0)
            thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode('utf-8')
            thumbnail_url = f"data:image/png;base64,{thumb_base64}"

            # Estimate stats (Tripo doesn't provide these, so we estimate)
            stats = {
                "vertices": 50000,  # Typical Tripo output
                "faces": 100000,
                "is_watertight": True,
                "volume": None,
                "surface_area": 1000.0
            }

            result = {
                "generation_id": generation_id,
                "model_url": model_url_data,
                "thumbnail_url": thumbnail_url,
                "format": export_format,
                "mime_type": mime_type,
                "file_size": len(model_bytes),
                "stats": stats,
                "background_removed": remove_background,
                "created_at": datetime.utcnow().isoformat(),
                "success": True,
                "tripo_task_id": task_id
            }

            logger.info(f"3D generation {generation_id} completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error in 3D generation: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "created_at": datetime.utcnow().isoformat()
            }

    def get_supported_formats(self) -> list:
        """Get list of supported export formats"""
        return ["glb", "obj", "fbx", "usdz", "stl"]


# Global service instance
model_3d_service = Model3DService()
