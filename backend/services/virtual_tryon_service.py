"""
Virtual Try-On Service using Gemini 2.5 Flash Image Preview
Implements AI-powered jewelry overlay using Gemini's image generation capabilities
"""
import google.generativeai as genai
from backend.app.config import settings
from typing import List, Dict, Optional, Tuple
import logging
import base64
import io
from PIL import Image
import os
from pathlib import Path
import httpx
import asyncio

logger = logging.getLogger(__name__)


class VirtualTryOnService:
    """Service for AI-powered virtual try-on using Gemini 2.5 Flash Image Preview"""

    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=settings.gemini_api_key)

        # Use Gemini 2.5 Flash with image generation capabilities
        self.model_name = "gemini-2.5-flash-image-preview"

        logger.info(f"🎨 Virtual Try-On Service initialized with {self.model_name}")

    def _image_to_base64(self, image: Image.Image) -> Tuple[str, str]:
        """
        Convert PIL Image to base64 string

        Args:
            image: PIL Image to convert

        Returns:
            Tuple of (base64_data, mime_type)
        """
        try:
            # Convert to RGB if needed
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')

            # Save to bytes buffer
            buffer = io.BytesIO()
            format_type = 'PNG' if image.mode == 'RGBA' else 'JPEG'
            image.save(buffer, format=format_type)

            # Get base64 encoding
            base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Determine MIME type
            mime_type = 'image/png' if format_type == 'PNG' else 'image/jpeg'

            logger.info(f"Converted image to base64. Size: {len(base64_data)} chars, MIME: {mime_type}")
            return base64_data, mime_type

        except Exception as e:
            logger.error(f"Error converting image to base64: {e}")
            raise

    async def _url_to_image(self, url: str) -> Image.Image:
        """
        Download image from URL and convert to PIL Image

        Args:
            url: Image URL

        Returns:
            PIL Image
        """
        try:
            logger.info(f"Fetching image from: {url}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; GemVisionBot/1.0)"},
                    follow_redirects=True
                )
                response.raise_for_status()

                image = Image.open(io.BytesIO(response.content))
                logger.info(f"Successfully loaded image. Size: {image.size}, Mode: {image.mode}")
                return image

        except Exception as e:
            logger.error(f"Error fetching image from {url}: {e}")
            raise

    async def generate_tryon_image(
        self,
        person_image: Image.Image,
        jewelry_image: Image.Image,
        jewelry_type: str = "jewelry",
        jewelry_description: str = ""
    ) -> Dict:
        """
        Generate virtual try-on image using Gemini 2.5 Flash Image Preview

        This uses Gemini's AI image generation to create a completely new image
        showing the person wearing the jewelry, rather than simple compositing.

        Args:
            person_image: PIL Image of the person
            jewelry_image: PIL Image of the jewelry
            jewelry_type: Type of jewelry (ring, bracelet, necklace, earring)
            jewelry_description: Additional description of the jewelry

        Returns:
            Dict with generated image and metadata
        """
        try:
            logger.info("=" * 80)
            logger.info("🎨 STARTING VIRTUAL TRY-ON GENERATION WITH GEMINI 2.5")
            logger.info("=" * 80)
            logger.info(f"📸 Person image size: {person_image.size}, mode: {person_image.mode}")
            logger.info(f"💍 Jewelry image size: {jewelry_image.size}, mode: {jewelry_image.mode}")
            logger.info(f"📋 Jewelry type: {jewelry_type}")
            logger.info(f"📝 Description: {jewelry_description}")
            logger.info("-" * 80)

            # Build the prompt (based on the Node.js version)
            prompt = f"""You are an expert jewelry visualization AI. I am providing you with two images: one of a person and one of a jewelry item. Please digitally place the jewelry onto the person and transform them into a professional model-like presentation.

[Attach person's image]
[Attach jewelry image]

Instructions:
1. Transform the person's pose to appear as a professional model in either:
   - Sitting straight on a chair with excellent posture and confident positioning, OR
   - Standing in an elegant, model-like pose with proper posture and poise
2. Identify the type of jewelry and determine the correct placement on the person (earrings on ears, necklace on neck, bracelet on wrist, ring on finger, etc.)
3. Scale the jewelry to realistic proportions that would fit the person naturally
4. Change the background to a solid color: #030344 (deep navy blue)
5. Ensure the person maintains a confident, professional model-like expression and body language
6. Match the lighting, shadows, and reflections of the jewelry to create professional studio lighting
7. Position the jewelry following natural body contours and realistic wearing angles
8. Adjust the jewelry's perspective to match the person's refined pose and camera angle
9. Blend seamlessly so the jewelry appears genuinely worn by the person
10. Preserve the jewelry's original design, materials, colors, and textures
11. Add appropriate shadows and highlights where the jewelry would naturally cast them
12. Create professional studio-quality lighting that complements the #030344 background

Create a high-quality, professional model-style composite image showing the person in either a sitting or standing pose, naturally wearing the jewelry piece against the specified background color."""

            # Convert images to base64
            logger.info("🔄 Converting images to base64...")
            person_b64, person_mime = self._image_to_base64(person_image)
            jewelry_b64, jewelry_mime = self._image_to_base64(jewelry_image)

            # Prepare request payload for Gemini API
            # Using the REST API format from the Node.js code
            parts = [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": person_mime,
                        "data": person_b64
                    }
                },
                {
                    "inline_data": {
                        "mime_type": jewelry_mime,
                        "data": jewelry_b64
                    }
                }
            ]

            request_payload = {
                "contents": [
                    {
                        "parts": parts
                    }
                ],
                "generationConfig": {
                    "temperature": 1.0
                }
            }

            logger.info("📤 Sending request to Gemini API...")

            # Make direct REST API call using httpx
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    api_url,
                    json=request_payload,
                    headers={
                        "x-goog-api-key": settings.gemini_api_key,
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                response_data = response.json()

            logger.info("✅ Received response from Gemini API")

            # Extract the base64 image data from response
            candidate = response_data.get("candidates", [{}])[0]
            if not candidate or "content" not in candidate or "parts" not in candidate["content"]:
                logger.error(f"Invalid response structure: {response_data}")
                raise ValueError("No content parts found in response")

            # Look for inline_data or inlineData in the response parts
            base64_image_data = None
            for part in candidate["content"]["parts"]:
                # Check for both camelCase (inlineData) and snake_case (inline_data) formats
                if "inlineData" in part and "data" in part["inlineData"]:
                    base64_image_data = part["inlineData"]["data"]
                    logger.info("Found image data in inlineData format")
                    break
                elif "inline_data" in part and "data" in part["inline_data"]:
                    base64_image_data = part["inline_data"]["data"]
                    logger.info("Found image data in inline_data format")
                    break

            if not base64_image_data:
                # Fallback: try to extract from the entire response text
                import json
                response_text = json.dumps(response_data)
                import re
                data_match = re.search(r'"data":\s*"([^"]*)"', response_text)
                if data_match:
                    base64_image_data = data_match.group(1)
                    logger.info("Found image data using fallback regex")

            if not base64_image_data:
                logger.error(f"Full response: {response_data}")
                raise ValueError("No image data found in response")

            # Decode base64 to PIL Image
            logger.info("🖼️  Decoding base64 image data...")
            image_bytes = base64.b64decode(base64_image_data)
            generated_image = Image.open(io.BytesIO(image_bytes))

            logger.info(f"✅ Generated image decoded. Size: {generated_image.size}, Mode: {generated_image.mode}")

            # Save the generated image locally
            import uuid
            import datetime

            logger.info("💾 Saving result to local storage...")
            storage_dir = Path(__file__).parent.parent / "storage" / "tryon"
            storage_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            result_filename = f"tryon_{timestamp}_{unique_id}.png"
            result_path = storage_dir / result_filename

            generated_image.save(result_path, format="PNG", quality=95)
            result_url = f"/storage/tryon/{result_filename}"

            logger.info(f"✅ Saved to: {result_path}")
            logger.info(f"   🌐 URL: {result_url}")

            # Upload to S3 if configured
            s3_url = None
            s3_key = None

            if hasattr(settings, 'aws_s3_bucket') and settings.aws_s3_bucket:
                try:
                    logger.info("☁️  Uploading to S3...")
                    import boto3

                    s3_client = boto3.client(
                        's3',
                        aws_access_key_id=settings.aws_access_key_id,
                        aws_secret_access_key=settings.aws_secret_access_key,
                        region_name=getattr(settings, 'aws_region', 'us-east-1')
                    )

                    s3_key = f"generated-images/{unique_id}.png"

                    with open(result_path, 'rb') as f:
                        s3_client.upload_fileobj(
                            f,
                            settings.aws_s3_bucket,
                            s3_key,
                            ExtraArgs={'ContentType': 'image/png'}
                        )

                    s3_url = f"https://{settings.aws_s3_bucket}.s3.amazonaws.com/{s3_key}"
                    logger.info(f"✅ Uploaded to S3: {s3_url}")

                    # Optionally delete local file if S3 upload successful
                    # os.remove(result_path)

                except Exception as e:
                    logger.warning(f"⚠️  S3 upload failed: {e}")
                    # Continue anyway with local file

            result = {
                "success": True,
                "result_url": s3_url or result_url,
                "local_url": result_url,
                "s3_url": s3_url,
                "s3_key": s3_key,
                "local_path": str(result_path),
                "size": len(image_bytes),
                "image_size": generated_image.size,
                "model_used": self.model_name,
                "jewelry_type": jewelry_type,
                "message": "Virtual try-on generated successfully with Gemini 2.5 Flash!",
                "generation_method": "gemini_ai_image_generation"
            }

            logger.info("=" * 80)
            logger.info("✨ VIRTUAL TRY-ON GENERATION COMPLETE!")
            logger.info("=" * 80)

            return result

        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ VIRTUAL TRY-ON GENERATION FAILED!")
            logger.error(f"💥 Error: {str(e)}")
            logger.error(f"📍 Error type: {type(e).__name__}")
            logger.error("=" * 80)
            import traceback
            logger.error(f"🔍 Traceback:\n{traceback.format_exc()}")
            raise

    async def generate_tryon(
        self,
        body_image: Image.Image,
        jewelry_image: Image.Image,
        jewelry_type: str,
        jewelry_description: str,
        target_area: Optional[str] = None,
        use_examples: bool = False,
        auto_detect: bool = False
    ) -> Dict:
        """
        Generate virtual try-on image (main entry point for compatibility)

        This method provides backward compatibility with the old interface
        while using the new Gemini AI image generation approach.

        Args:
            body_image: PIL Image (can be hand, neck, full body, etc.)
            jewelry_image: PIL Image of the jewelry design
            jewelry_type: Type of jewelry (ring, bracelet, necklace, earring)
            jewelry_description: Text description of the jewelry
            target_area: Specific placement area (ignored - AI determines this)
            use_examples: Whether to use few-shot learning (ignored in new version)
            auto_detect: Whether to auto-detect body part (ignored - AI does this)

        Returns:
            Dict with generated image and metadata
        """
        # Simply delegate to the new AI generation method
        return await self.generate_tryon_image(
            person_image=body_image,
            jewelry_image=jewelry_image,
            jewelry_type=jewelry_type,
            jewelry_description=jewelry_description
        )


# Global service instance
virtual_tryon_service = VirtualTryOnService()
