"""
AI Jewellery Designer Service
Handles text-to-image generation for jewellery designs using Gemini Imagen 3
Cost-efficient implementation: $0.03 per image with Imagen 3
"""
from anthropic import Anthropic
import google.generativeai as genai
from google import genai as google_genai
from google.genai import types
from backend.app.config import settings
from backend.services.s3_service import s3_service
from typing import List, Dict, Optional
import logging
import uuid
from datetime import datetime
import json
import base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

logger = logging.getLogger(__name__)

# Initialize AI clients
anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
genai.configure(api_key=settings.gemini_api_key)

# Initialize Google GenAI client for Imagen 3
try:
    genai_client = google_genai.Client(api_key=settings.gemini_api_key)
    logger.info("✅ Google GenAI client initialized for Imagen 3")
except Exception as e:
    logger.warning(f"⚠️ Could not initialize Google GenAI client: {e}")
    genai_client = None


class AIDesignerService:
    """Service for generating jewellery designs using AI"""

    # Prompt templates for different categories and styles
    CATEGORY_TEMPLATES = {
        "ring": "ring with {motif}, {stone_description}, band style: {band_style}",
        "necklace": "necklace with {motif}, {stone_description}, chain style: {chain_style}",
        "earring": "pair of earrings with {motif}, {stone_description}, backing: {backing_type}",
        "bracelet": "bracelet with {motif}, {stone_description}, clasp: {clasp_type}"
    }

    STYLE_PRESETS = {
        "bridal": {
            "keywords": "elegant, romantic, timeless, pavé, halo, brilliant cut",
            "typical_stones": "diamond, white gold, platinum"
        },
        "minimalist": {
            "keywords": "simple, clean lines, modern, sleek, understated",
            "typical_stones": "single stone, thin band, polished"
        },
        "traditional": {
            "keywords": "ornate, heritage, intricate, filigree, detailed",
            "typical_stones": "gold, colored gemstones, granulation"
        },
        "antique": {
            "keywords": "vintage, art deco, Victorian, engraved, milgrain",
            "typical_stones": "old cut diamonds, rose gold, oxidized"
        },
        "heavy-stone": {
            "keywords": "bold, statement, large center stone, dramatic, cocktail",
            "typical_stones": "large gemstones, multi-stone, cluster"
        }
    }

    REALISM_MODES = {
        "realistic": "Photorealistic professional jewelry photography, studio lighting, white background, 8k resolution",
        "photoreal": "Ultra-realistic 3D render, ray-traced, professional product photography, studio lighting, white background",
        "cad": "CAD-style technical drawing, line art, blueprint style, clean vector illustration, white background",
        "sketch": "Hand-drawn jewelry sketch, pencil drawing, designer sketch style, artistic rendering"
    }

    def __init__(self):
        # Cost-efficient Imagen 3 model: $0.03 per image
        self.default_model = "imagen-3.0-generate-001"
        self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.genai_client = genai_client
        logger.info("💎 AI Designer Service initialized with Imagen 3")
        logger.info(f"   🎨 Image generation: {self.default_model} ($0.03/image)")
        logger.info(f"   📊 Analysis model: gemini-2.0-flash-exp")

    def enhance_prompt(
        self,
        base_prompt: str,
        category: str,
        style_preset: str,
        realism_mode: str = "realistic"
    ) -> str:
        """
        Enhance user prompt with category and style-specific keywords

        Args:
            base_prompt: User's input prompt
            category: Jewellery category
            style_preset: Style preset name
            realism_mode: Realism mode

        Returns:
            Enhanced prompt string
        """
        # Get style keywords
        style_info = self.STYLE_PRESETS.get(style_preset.lower(), {})
        style_keywords = style_info.get("keywords", "")

        # Get realism prefix
        realism_prefix = self.REALISM_MODES.get(realism_mode.lower(), self.REALISM_MODES["realistic"])

        # Build enhanced prompt
        enhanced = f"{realism_prefix}, {category} jewelry: {base_prompt}"

        if style_keywords:
            enhanced += f", style: {style_keywords}"

        # Add quality suffixes
        enhanced += ", professional jewelry design, high detail, commercial photography quality"

        logger.info(f"Enhanced prompt: {enhanced}")
        return enhanced

    async def _generate_placeholder_images(
        self,
        prompt: str,
        num_images: int,
        storage_dir: Path
    ) -> List[Dict]:
        """Generate placeholder images when API key is not available"""
        logger.info(f"📋 Generating {num_images} placeholder jewelry design(s)...")
        results = []

        for i in range(num_images):
            seed = f"placeholder_{uuid.uuid4().hex[:8]}"
            filename = f"design_{seed}.png"
            filepath = storage_dir / filename

            # Create placeholder with prompt text
            img = Image.new('RGB', (1024, 1024), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)

            # Add border
            draw.rectangle([(10, 10), (1014, 1014)], outline=(200, 200, 200), width=3)

            # Add title
            try:
                title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
                text_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
            except:
                title_font = ImageFont.load_default()
                text_font = ImageFont.load_default()

            # Draw text
            draw.text((512, 100), "Jewelry Design Preview", fill=(100, 100, 100), anchor="mm", font=title_font)
            draw.text((512, 150), f"Design #{i+1}", fill=(150, 150, 150), anchor="mm", font=text_font)
            draw.text((512, 200), "AI image generation coming soon", fill=(100, 150, 100), anchor="mm", font=text_font)

            # Add wrapped prompt
            y_pos = 280
            words = prompt.split()
            line = ""
            for word in words[:50]:
                test_line = line + word + " "
                if len(test_line) > 55:
                    draw.text((512, y_pos), line, fill=(100, 100, 100), anchor="mm", font=text_font)
                    line = word + " "
                    y_pos += 30
                else:
                    line = test_line
            if line:
                draw.text((512, y_pos), line, fill=(100, 100, 100), anchor="mm", font=text_font)

            # Save
            img.save(filepath, 'PNG')
            # Use full backend URL so frontend can access the image
            local_url = f"http://localhost:8000/storage/designs/{filename}"

            logger.info(f"✅ Generated placeholder {i+1}/{num_images}: {local_url}")

            results.append({
                "url": local_url,
                "s3_key": None,
                "revised_prompt": prompt,
                "model": "placeholder",
                "seed": seed
            })

        return results

    async def generate_with_gemini(
        self,
        prompt: str,
        num_images: int = 4,
        size: str = "1024x1024",
        quality: str = "hd"
    ) -> List[Dict]:
        """
        Generate images using Gemini Imagen 3 - Cost: $0.03 per image

        Args:
            prompt: Enhanced prompt
            num_images: Number of images to generate (max 4)
            size: Image size - supports 1:1, 3:4, 4:3, 9:16, 16:9
            quality: Image quality

        Returns:
            List of generated image data with local URLs
        """
        try:
            logger.info(f"💎 Generating {num_images} jewelry design(s) with Imagen 3...")
            logger.info(f"📝 Prompt: {prompt[:200]}...")
            logger.info(f"💰 Estimated cost: ${num_images * 0.03:.2f}")

            results = []

            # Create local storage directory
            storage_dir = Path(__file__).parent.parent / "storage" / "designs"
            storage_dir.mkdir(parents=True, exist_ok=True)

            # Check if GenAI client is available - if not, use placeholder mode
            if not self.genai_client:
                logger.warning("⚠️ GEMINI_API_KEY not set - using placeholder mode")
                logger.warning("💡 To use real AI image generation, add GEMINI_API_KEY to .env file")
                return await self._generate_placeholder_images(prompt, num_images, storage_dir)

            # Convert size to aspect ratio
            aspect_ratio_map = {
                "1024x1024": "1:1",
                "768x1024": "3:4",
                "1024x768": "4:3",
                "576x1024": "9:16",
                "1024x576": "16:9"
            }
            aspect_ratio = aspect_ratio_map.get(size, "1:1")

            # Generate all images in one request for cost efficiency
            logger.info(f"🎨 Calling Imagen 3 API with aspect ratio {aspect_ratio}...")

            response = self.genai_client.models.generate_images(
                model='imagen-3.0-generate-002',  # Use latest Imagen 3 model
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=num_images,
                    output_mime_type="image/jpeg",
                    safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
                    person_generation="DONT_ALLOW",  # No people in jewelry photos
                    aspect_ratio=aspect_ratio
                )
            )

            # Save each generated image
            for i, generated_image in enumerate(response.generated_images):
                seed = f"imagen3_{uuid.uuid4().hex[:8]}"
                filename = f"design_{seed}.jpg"
                filepath = storage_dir / filename

                # Save the image
                generated_image.image.save(str(filepath), "JPEG", quality=95)

                # Generate full backend URL so frontend can access the image
                local_url = f"http://localhost:8000/storage/designs/{filename}"

                logger.info(f"✅ Generated image {i+1}/{num_images}: {local_url}")

                results.append({
                    "url": local_url,
                    "s3_key": None,  # Not using S3
                    "revised_prompt": prompt,
                    "model": self.default_model,
                    "seed": seed
                })

            if not results:
                raise Exception("Failed to generate any images")

            logger.info(f"✅ Successfully generated {len(results)} images with Imagen 3")
            logger.info(f"💰 Total cost: ${len(results) * 0.03:.2f}")
            return results

        except Exception as e:
            logger.error(f"❌ Error generating with Imagen 3: {e}")
            logger.error(f"💡 Make sure GEMINI_API_KEY is set in .env file")
            raise

    async def analyze_design_with_claude(
        self,
        image_url: str,
        prompt: str
    ) -> Dict:
        """
        Use Claude to analyze generated design and extract metadata

        Args:
            image_url: URL of generated image
            prompt: Original prompt

        Returns:
            Analysis results with materials, colors, etc.
        """
        try:
            # Use Claude's vision capabilities to analyze the image
            message = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": image_url
                                }
                            },
                            {
                                "type": "text",
                                "text": f"""Analyze this jewelry design and extract the following information in JSON format:
                                {{
                                  "materials": ["list of materials detected, e.g., gold, diamond, platinum"],
                                  "colors": ["dominant colors"],
                                  "style_attributes": ["style characteristics"],
                                  "stone_count": "estimated number of stones",
                                  "confidence": 0.0-1.0
                                }}

                                Original prompt: {prompt}
                                """
                            }
                        ]
                    }
                ]
            )

            # Parse response
            response_text = message.content[0].text

            # Try to extract JSON from response
            try:
                # Find JSON in the response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end > start:
                    analysis = json.loads(response_text[start:end])
                else:
                    analysis = {
                        "materials": ["gold", "diamond"],
                        "colors": ["gold", "white"],
                        "confidence": 0.7
                    }
            except:
                analysis = {
                    "materials": ["gold", "diamond"],
                    "colors": ["gold", "white"],
                    "confidence": 0.7
                }

            logger.info(f"Analyzed design with Claude: {analysis}")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing with Claude: {e}")
            # Return default analysis
            return {
                "materials": ["gold", "diamond"],
                "colors": ["gold", "white"],
                "confidence": 0.5
            }

    async def generate_design(
        self,
        prompt: str,
        category: str,
        style_preset: str,
        realism_mode: str = "realistic",
        num_images: int = 4
    ) -> Dict:
        """
        Main method to generate jewellery design

        Args:
            prompt: User's prompt
            category: Jewellery category
            style_preset: Style preset
            realism_mode: Realism mode
            num_images: Number of images to generate

        Returns:
            Complete generation result with images and metadata
        """
        try:
            # Enhance prompt
            enhanced_prompt = self.enhance_prompt(
                prompt, category, style_preset, realism_mode
            )

            # Generate images with Gemini Imagen 3
            images = await self.generate_with_gemini(
                enhanced_prompt,
                num_images=min(num_images, settings.max_images_per_generation),
                size=settings.image_size,
                quality=settings.image_quality
            )

            # Analyze first image with Claude
            if images:
                analysis = await self.analyze_design_with_claude(
                    images[0]["url"],
                    enhanced_prompt
                )
            else:
                analysis = {}

            # Create generation result
            generation_id = f"gen_{uuid.uuid4().hex}"

            result = {
                "generation_id": generation_id,
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "category": category,
                "style_preset": style_preset,
                "realism_mode": realism_mode,
                "images": images,
                "analysis": analysis,
                "materials": analysis.get("materials", []),
                "colors": analysis.get("colors", []),
                "confidence": analysis.get("confidence", 0.5),
                "model": self.default_model,
                "created_at": datetime.utcnow().isoformat()
            }

            logger.info(f"Generated design: {generation_id}")
            return result

        except Exception as e:
            logger.error(f"Error generating design: {e}")
            raise

    def get_template_prompts(self, category: str, style_preset: str) -> List[str]:
        """
        Get template prompts for a category and style

        Args:
            category: Jewellery category
            style_preset: Style preset

        Returns:
            List of template prompts
        """
        templates = {
            "ring": {
                "bridal": [
                    "solitaire engagement ring with round brilliant diamond, thin pavé band, 18k white gold",
                    "halo engagement ring with cushion cut center diamond, rose gold band with micro pavé",
                    "three-stone engagement ring with emerald cut center, platinum setting"
                ],
                "minimalist": [
                    "simple solitaire ring with round diamond, thin polished band, 14k yellow gold",
                    "bezel set diamond ring, sleek modern design, brushed finish",
                    "thin band with single floating diamond, minimal setting"
                ],
                "traditional": [
                    "ornate gold ring with filigree work, ruby center stone, intricate band details",
                    "heritage design ring with granulation, multiple small diamonds, 22k gold",
                    "traditional Indian ring with temple motifs, emerald center, detailed engraving"
                ]
            },
            "necklace": {
                "bridal": [
                    "diamond pendant necklace with teardrop design, delicate chain, white gold",
                    "solitaire diamond pendant, classic round cut, simple chain, platinum",
                    "halo pendant necklace with pear-shaped diamond, micro pavé halo"
                ],
                "minimalist": [
                    "simple gold chain with small diamond pendant, delicate and modern",
                    "single pearl pendant on thin gold chain, minimalist design",
                    "small geometric pendant, clean lines, brushed metal finish"
                ]
            }
        }

        return templates.get(category, {}).get(style_preset, [
            f"Beautiful {style_preset} style {category}",
            f"Elegant {category} with modern design",
            f"Classic {style_preset} {category} with fine details"
        ])


# Global service instance
ai_designer_service = AIDesignerService()
