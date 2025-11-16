"""
AI Jewellery Designer Service
Handles text-to-image generation for jewellery designs using various AI models
"""
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
from backend.app.config import settings
from backend.services.s3_service import s3_service
from typing import List, Dict, Optional
import logging
import uuid
from datetime import datetime
import json
import base64

logger = logging.getLogger(__name__)

# Initialize AI clients
openai_client = OpenAI(api_key=settings.openai_api_key)
anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
genai.configure(api_key=settings.gemini_api_key)


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
        self.default_model = settings.default_image_model

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

    async def generate_with_dalle(
        self,
        prompt: str,
        num_images: int = 4,
        size: str = "1024x1024",
        quality: str = "hd"
    ) -> List[Dict]:
        """
        Generate images using DALL-E and upload to S3

        Args:
            prompt: Enhanced prompt
            num_images: Number of images to generate
            size: Image size
            quality: Image quality

        Returns:
            List of generated image data with S3 URLs
        """
        try:
            # DALL-E 3 only supports 1 image per request
            if self.default_model == "dall-e-3":
                num_images = min(num_images, 1)

            results = []

            for i in range(num_images):
                # Request base64 encoded image instead of URL
                response = openai_client.images.generate(
                    model=self.default_model,
                    prompt=prompt,
                    size=size,
                    quality=quality if self.default_model == "dall-e-3" else "standard",
                    n=1,
                    response_format="b64_json"  # Request base64 format
                )

                for image in response.data:
                    # Decode base64 image
                    image_data = base64.b64decode(image.b64_json)

                    # Upload to S3
                    seed = f"dalle_{uuid.uuid4().hex[:8]}"
                    filename = f"design_{seed}.png"
                    s3_url, s3_key = s3_service.upload_image(
                        image_data=image_data,
                        folder="designs",
                        filename=filename,
                        content_type="image/png"
                    )

                    logger.info(f"Uploaded image to S3: {s3_url}")

                    results.append({
                        "url": s3_url,  # Use S3 URL instead of DALL-E URL
                        "s3_key": s3_key,
                        "revised_prompt": getattr(image, 'revised_prompt', prompt),
                        "model": self.default_model,
                        "seed": seed
                    })

            logger.info(f"Generated {len(results)} images with DALL-E and uploaded to S3")
            return results

        except Exception as e:
            logger.error(f"Error generating with DALL-E: {e}")
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

            # Generate images
            images = await self.generate_with_dalle(
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
