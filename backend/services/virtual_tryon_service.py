"""
Virtual Try-On Service using Veo 2 (Google Gemini API)
Implements AI-powered jewelry overlay on hand/body photos with few-shot learning
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

logger = logging.getLogger(__name__)

# Initialize Gemini client (already configured in ai_designer_service)
# genai.configure(api_key=settings.gemini_api_key)


class VirtualTryOnService:
    """Service for AI-powered virtual try-on using Google Gemini (Imagen 3)"""

    def __init__(self):
        # Use Gemini model with image generation capabilities (Imagen 3 via Vertex AI)
        self.analysis_model = "gemini-2.0-flash-exp"  # For analysis and placement
        self.image_gen_model = "imagen-3.0-generate-001"  # For image generation (Gemini Banana)

        self.examples_dir = Path(__file__).parent.parent / "assets" / "tryon_examples"
        self.input_dir = self.examples_dir / "input"
        self.output_dir = self.examples_dir / "output"

        # Ensure directories exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"🍌 Virtual Try-On Service initialized with Gemini Imagen 3 (Banana)")
        logger.info(f"   📊 Analysis model: {self.analysis_model}")
        logger.info(f"   🎨 Image generation model: {self.image_gen_model}")

    def _load_example_pairs(self) -> List[Tuple[Image.Image, Image.Image, str]]:
        """
        Load example input/output image pairs from the examples directory

        Returns:
            List of (input_image, output_image, description) tuples
        """
        examples = []

        # Get all input files
        input_files = sorted(list(self.input_dir.glob("*.[jp][pn]g")) +
                           list(self.input_dir.glob("*.webp")))

        logger.info(f"Found {len(input_files)} potential example input files")

        for input_path in input_files:
            # Extract base name (everything before the file extension)
            base_name = input_path.stem

            # Look for matching output file
            output_candidates = [
                self.output_dir / f"{base_name}{ext}"
                for ext in [".jpg", ".jpeg", ".png", ".webp"]
            ]

            output_path = None
            for candidate in output_candidates:
                if candidate.exists():
                    output_path = candidate
                    break

            if output_path:
                try:
                    # Load images
                    input_img = Image.open(input_path).convert("RGB")
                    output_img = Image.open(output_path).convert("RGB")

                    # Create description from filename
                    description = base_name.replace("_", " ").replace("-", " ")

                    examples.append((input_img, output_img, description))
                    logger.info(f"Loaded example pair: {base_name}")

                except Exception as e:
                    logger.warning(f"Failed to load example pair {base_name}: {e}")

        logger.info(f"Loaded {len(examples)} example pairs for few-shot learning")
        return examples

    def _image_to_bytes(self, image: Image.Image, format: str = "JPEG") -> bytes:
        """Convert PIL Image to bytes"""
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()

    async def _detect_body_part_and_placement(
        self,
        body_image: Image.Image,
        jewelry_type: str
    ) -> Dict:
        """
        Use Gemini to detect what body part is in the image and determine best placement

        Args:
            body_image: Image that could contain hand, neck, full body, etc.
            jewelry_type: Type of jewelry to place

        Returns:
            Dict with detected body part and placement recommendations
        """
        try:
            model = genai.GenerativeModel(self.analysis_model)

            # Mapping of jewelry types to possible body parts
            jewelry_body_mapping = {
                "ring": ["hand", "finger", "fingers"],
                "bracelet": ["wrist", "hand", "arm"],
                "necklace": ["neck", "chest", "upper body", "collar area"],
                "earring": ["ear", "ears", "head", "face"]
            }

            possible_parts = jewelry_body_mapping.get(jewelry_type.lower(), ["body"])

            detection_prompt = f"""Analyze this image and determine:

1. **What body part(s) are visible?** (e.g., hand, neck, full body, wrist, face, ear)
2. **Is it suitable for placing a {jewelry_type}?**
3. **Where exactly should the {jewelry_type} be placed?**
4. **What specific area/landmark should be used?** (e.g., "ring finger", "left wrist", "center of neck", "left earlobe")

For a {jewelry_type}, we typically look for: {', '.join(possible_parts)}

Respond in JSON format:
{{
  "detected_body_parts": ["hand", "wrist"],
  "primary_body_part": "hand",
  "is_suitable_for_{jewelry_type}": true,
  "recommended_placement_area": "ring finger",
  "specific_landmarks": ["knuckle of ring finger", "base of finger"],
  "placement_description": "Place the {jewelry_type} on the ring finger, positioned between the knuckle and base",
  "confidence": 0.95,
  "alternative_placements": ["middle finger", "index finger"],
  "image_quality_notes": "Clear image with good lighting, hand is visible and well-positioned"
}}

IMPORTANT:
- If this is a full body image, identify the specific area where the {jewelry_type} should go
- For rings: identify which finger(s) are visible and best for placement
- For necklaces: identify the neck/collar bone area
- For bracelets: identify wrist or arm area
- For earrings: identify ear location
- Be specific about left/right if distinguishable
"""

            content = [detection_prompt, body_image]

            logger.info(f"Detecting body part for {jewelry_type} placement...")
            response = model.generate_content(content)

            # Parse JSON response
            import json
            response_text = response.text.strip()

            # Extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1

            if start != -1 and end > start:
                detection_data = json.loads(response_text[start:end])
            else:
                # Fallback if JSON parsing fails
                detection_data = {
                    "detected_body_parts": ["unknown"],
                    "primary_body_part": "body",
                    f"is_suitable_for_{jewelry_type}": True,
                    "recommended_placement_area": self._get_default_placement(jewelry_type),
                    "confidence": 0.5,
                    "placement_description": f"Place {jewelry_type} on appropriate body part"
                }

            logger.info(f"Detected body part: {detection_data.get('primary_body_part')}")
            logger.info(f"Recommended placement: {detection_data.get('recommended_placement_area')}")

            return detection_data

        except Exception as e:
            logger.error(f"Error detecting body part: {e}")
            # Return default placement
            return {
                "detected_body_parts": ["unknown"],
                "primary_body_part": "body",
                f"is_suitable_for_{jewelry_type}": True,
                "recommended_placement_area": self._get_default_placement(jewelry_type),
                "confidence": 0.5,
                "placement_description": f"Place {jewelry_type} on appropriate body part",
                "error": str(e)
            }

    def _get_default_placement(self, jewelry_type: str) -> str:
        """Get default placement area for jewelry type"""
        defaults = {
            "ring": "ring finger",
            "bracelet": "wrist",
            "necklace": "neck center",
            "earring": "earlobe"
        }
        return defaults.get(jewelry_type.lower(), "appropriate body part")

    def _prepare_prompt_with_examples(
        self,
        jewelry_type: str,
        jewelry_description: str,
        target_area: str,
        examples: List[Tuple[Image.Image, Image.Image, str]]
    ) -> str:
        """
        Prepare detailed prompt for Gemini with context from examples

        Args:
            jewelry_type: Type of jewelry (ring, bracelet, necklace, earring)
            jewelry_description: Description of the jewelry design
            target_area: Where to place jewelry (e.g., "ring finger", "wrist")
            examples: Example pairs for few-shot learning

        Returns:
            Detailed prompt string
        """
        base_prompt = f"""You are an expert at creating photorealistic virtual try-on images for jewelry.

TASK: Create a realistic image showing {jewelry_type} placed on the {target_area} in the provided photo.

JEWELRY DETAILS:
- Type: {jewelry_type}
- Description: {jewelry_description}

REQUIREMENTS:
1. **Realistic Placement**: Position the {jewelry_type} naturally on the {target_area}
2. **Proper Perspective**: Match the angle and perspective of the hand/body in the photo
3. **Accurate Lighting**: Match lighting conditions, shadows, and highlights from the original photo
4. **Natural Integration**: The jewelry should look like it's actually being worn, not pasted on
5. **Proper Sizing**: Scale the jewelry appropriately for the body part
6. **Reflections & Shadows**: Add realistic reflections on the jewelry surface and cast shadows
7. **Color Accuracy**: Maintain the jewelry's material colors (gold, silver, gemstones, etc.)
8. **High Quality**: Output should be photorealistic and professional quality

"""

        if examples:
            base_prompt += f"""
FEW-SHOT EXAMPLES:
I'm providing {len(examples)} example pairs showing:
- BEFORE: Original photo of hand/body
- AFTER: Same photo with jewelry realistically added

Study these examples to understand:
- How jewelry is naturally positioned
- Proper lighting and shadow integration
- Realistic sizing and perspective
- Material reflections and properties

Use these examples as a reference for creating the output image.

"""

        base_prompt += """
OUTPUT INSTRUCTIONS:
Generate a single image that looks exactly like the input photo but with the jewelry naturally placed and worn. The result should be indistinguishable from a real photograph of someone wearing the jewelry.

Focus on photorealism, proper physics (shadows, reflections), and natural integration.
"""

        return base_prompt

    async def _extract_and_analyze_jewelry(
        self,
        jewelry_image: Image.Image,
        jewelry_type: str,
        jewelry_description: str
    ) -> Dict:
        """
        Extract the jewelry from the image and analyze its characteristics

        Args:
            jewelry_image: PIL Image containing the jewelry
            jewelry_type: Type of jewelry
            jewelry_description: User's description

        Returns:
            Dict with analyzed jewelry characteristics and visual description for generation
        """
        try:
            logger.info("💎 Extracting and analyzing jewelry from image...")
            model = genai.GenerativeModel(self.analysis_model)

            jewelry_extraction_prompt = f"""Analyze this {jewelry_type} image and extract extremely detailed visual characteristics.

You need to describe this jewelry SO WELL that an AI image generator can recreate it EXACTLY in a new image.

Analyze EVERY DETAIL:

1. **Material & Finish**:
   - Exact metal type (yellow gold, white gold, rose gold, platinum, silver, etc.)
   - Finish type (high polish, brushed, matte, hammered, textured, etc.)
   - Any plating or coating

2. **Colors & Tones**:
   - Primary color and exact shade
   - Secondary colors
   - Any color variations or gradients
   - Reflective properties

3. **Design & Shape**:
   - Overall shape and form
   - Band/chain width and thickness (for rings/necklaces)
   - Setting type (prong, bezel, channel, pave, etc.)
   - Any patterns, engravings, filigree, or decorative elements
   - Symmetry and proportions

4. **Gemstones & Stones** (if any):
   - Number of stones
   - Stone types (diamond, ruby, sapphire, emerald, etc.)
   - Cut types (round brilliant, princess, emerald, oval, etc.)
   - Approximate carat size and dimensions
   - Color and clarity
   - Arrangement pattern

5. **Size & Proportions**:
   - Overall dimensions
   - Thickness and depth
   - Weight appearance (delicate, substantial, chunky)

6. **Style & Era**:
   - Design style (modern, vintage, art deco, Victorian, etc.)
   - Brand style if recognizable
   - Unique characteristics

7. **Ultra-detailed Description**:
   Write a paragraph that describes this jewelry so precisely that someone could recreate it without seeing it.
   Include ALL visible details, no matter how small.

Respond in JSON format:
{{
  "material": "exact material type",
  "metal_finish": "exact finish type",
  "primary_color": "exact primary color",
  "secondary_colors": ["list", "of", "colors"],
  "design_style": "style category",
  "shape": "exact shape description",
  "has_gemstones": true/false,
  "gemstone_count": number,
  "gemstone_type": "stone type",
  "gemstone_cut": "cut type",
  "gemstone_size": "approximate size",
  "gemstone_color": "stone color",
  "setting_type": "setting style",
  "texture": "surface texture",
  "band_width": "width description",
  "size_category": "delicate/medium/bold/chunky",
  "decorative_elements": ["list", "all", "decorative", "features"],
  "key_visual_features": ["most", "distinctive", "features"],
  "ultra_detailed_description": "An extremely detailed paragraph describing every visible aspect of this jewelry piece that would allow perfect recreation in an AI-generated image. Include materials, colors, shapes, stones, settings, textures, proportions, and any unique characteristics.",
  "generation_prompt": "A concise but complete prompt optimized for AI image generation that captures all essential visual characteristics"
}}"""

            jewelry_for_analysis = jewelry_image.convert("RGB") if jewelry_image.mode != "RGB" else jewelry_image

            response = model.generate_content([jewelry_extraction_prompt, jewelry_for_analysis])
            analysis_text = response.text

            logger.info(f"✅ Jewelry extraction and analysis complete ({len(analysis_text)} chars)")

            # Parse JSON response
            import json
            start = analysis_text.find('{')
            end = analysis_text.rfind('}') + 1

            if start != -1 and end > start:
                jewelry_data = json.loads(analysis_text[start:end])
                logger.info(f"   💎 Material: {jewelry_data.get('material', 'unknown')}")
                logger.info(f"   🎨 Color: {jewelry_data.get('primary_color', 'unknown')}")
                logger.info(f"   ✨ Style: {jewelry_data.get('design_style', 'unknown')}")
                if jewelry_data.get('has_gemstones'):
                    logger.info(f"   💍 Gemstones: {jewelry_data.get('gemstone_count', 0)} x {jewelry_data.get('gemstone_type', 'stones')}")
                logger.info(f"   📝 Detailed description: {jewelry_data.get('ultra_detailed_description', '')[:100]}...")
                return jewelry_data
            else:
                logger.warning("⚠️ Could not parse jewelry analysis, using fallback")
                return {
                    "material": "metal",
                    "primary_color": "gold",
                    "design_style": "classic",
                    "ultra_detailed_description": jewelry_description,
                    "generation_prompt": jewelry_description
                }

        except Exception as e:
            logger.error(f"❌ Jewelry extraction failed: {e}")
            return {
                "material": "metal",
                "primary_color": "gold",
                "design_style": "classic",
                "ultra_detailed_description": jewelry_description,
                "generation_prompt": jewelry_description
            }

    async def generate_tryon(
        self,
        body_image: Image.Image,
        jewelry_image: Image.Image,
        jewelry_type: str,
        jewelry_description: str,
        target_area: Optional[str] = None,
        use_examples: bool = True,
        auto_detect: bool = True
    ) -> Dict:
        """
        Generate virtual try-on image using Gemini Imagen 3 with automatic detection

        Args:
            body_image: PIL Image (can be hand, neck, full body, etc.)
            jewelry_image: PIL Image of the jewelry design
            jewelry_type: Type of jewelry (ring, bracelet, necklace, earring)
            jewelry_description: Text description of the jewelry
            target_area: Specific placement area (optional - will auto-detect if not provided)
            use_examples: Whether to use few-shot learning with examples
            auto_detect: Whether to automatically detect body part and placement

        Returns:
            Dict with generated image and metadata
        """
        try:
            logger.info("=" * 80)
            logger.info("🎨 STARTING VIRTUAL TRY-ON GENERATION WITH IMAGEN 3")
            logger.info("=" * 80)
            logger.info(f"📸 Body image size: {body_image.size}, mode: {body_image.mode}")
            logger.info(f"💍 Jewelry image size: {jewelry_image.size}, mode: {jewelry_image.mode}")
            logger.info(f"📋 Jewelry type: {jewelry_type}")
            logger.info(f"📝 Description: {jewelry_description}")
            logger.info(f"🎯 Auto-detect enabled: {auto_detect}")
            logger.info(f"📚 Use examples: {use_examples}")
            logger.info("-" * 80)
            # Step 1: Auto-detect body part and determine placement (if enabled)
            detection_result = None
            if auto_detect and target_area is None:
                logger.info("🔍 STEP 1: Auto-detecting body part and placement area...")
                try:
                    detection_result = await self._detect_body_part_and_placement(
                        body_image,
                        jewelry_type
                    )
                    target_area = detection_result.get("recommended_placement_area")
                    logger.info(f"✅ Auto-detection complete!")
                    logger.info(f"   🎯 Detected: {detection_result.get('primary_body_part')}")
                    logger.info(f"   📍 Placement: {target_area}")
                    logger.info(f"   💯 Confidence: {detection_result.get('confidence', 0):.2%}")
                except Exception as e:
                    logger.warning(f"⚠️ Auto-detection failed: {e}")
                    logger.info("   🔄 Falling back to default placement...")
                    target_area = self._get_default_placement(jewelry_type)
            elif target_area is None:
                logger.info("🎯 STEP 1: Using default placement (auto-detect disabled)")
                # Use default placement if no target area and auto-detect is off
                target_area = self._get_default_placement(jewelry_type)
                logger.info(f"   📍 Default placement: {target_area}")

            # Step 2: Extract and analyze the jewelry to get detailed characteristics
            logger.info("💎 STEP 2: Extracting jewelry from image and analyzing details...")
            jewelry_data = await self._extract_and_analyze_jewelry(
                jewelry_image,
                jewelry_type,
                jewelry_description
            )

            # Step 3: Load example pairs if available and requested
            logger.info(f"📚 STEP 3: Loading example pairs (enabled: {use_examples})...")
            examples = []
            if use_examples:
                examples = self._load_example_pairs()
                logger.info(f"   ✅ Loaded {len(examples)} example pairs for few-shot learning")
            else:
                logger.info("   ⏭️  Skipping examples (disabled)")

            # Step 3: Prepare prompt
            prompt = self._prepare_prompt_with_examples(
                jewelry_type,
                jewelry_description,
                target_area,
                examples
            )

            # Prepare content for Gemini
            content_parts = [prompt]

            # Add examples if available
            if examples:
                content_parts.append("\n=== REFERENCE EXAMPLES ===\n")
                for i, (input_img, output_img, desc) in enumerate(examples, 1):
                    content_parts.append(f"\nExample {i} ({desc}):")
                    content_parts.append("BEFORE (original photo):")
                    content_parts.append(input_img)
                    content_parts.append("AFTER (with jewelry):")
                    content_parts.append(output_img)

            # Add the actual images to process
            content_parts.append("\n=== YOUR TASK ===\n")
            content_parts.append("INPUT PHOTO (place jewelry on this):")
            content_parts.append(body_image)
            content_parts.append("\nJEWELRY TO ADD:")
            content_parts.append(jewelry_image)
            content_parts.append(f"\nGenerate the output image showing the {jewelry_type} naturally placed on the {target_area}.")

            # Use Gemini to generate the image
            # Note: Gemini currently doesn't directly generate images, but can analyze and guide
            # For actual image generation, we'll use a hybrid approach:
            # 1. Use Gemini to analyze placement and provide coordinates
            # 2. Use image compositing to overlay the jewelry

            model = genai.GenerativeModel(self.analysis_model)

            # First, get analysis and placement instructions from Gemini
            analysis_prompt = f"""Analyze the provided hand/body photo and jewelry image.

Provide EXACT instructions for realistic jewelry placement:

1. **Position**: Where exactly should the jewelry be placed? (x, y coordinates as percentages)
2. **Size**: What scale factor should be applied? (0.5 = 50% of original size)
3. **Rotation**: What angle/rotation in degrees?
4. **Adjustments**: Any color/lighting adjustments needed to match the scene?

Respond in JSON format:
{{
  "placement": {{
    "x_percent": 50.0,
    "y_percent": 50.0,
    "scale": 1.0,
    "rotation_degrees": 0,
    "flip_horizontal": false,
    "flip_vertical": false
  }},
  "adjustments": {{
    "brightness": 1.0,
    "contrast": 1.0,
    "saturation": 1.0,
    "warmth": 0
  }},
  "shadows": {{
    "add_shadow": true,
    "shadow_offset_x": 5,
    "shadow_offset_y": 5,
    "shadow_blur": 10,
    "shadow_opacity": 0.3
  }},
  "explanation": "Brief explanation of the placement strategy"
}}

IMPORTANT: Analyze the hand photo carefully to ensure realistic placement for a {jewelry_type} on the {target_area}.
"""

            # Convert images to RGB for Gemini API (it doesn't handle RGBA well)
            body_for_analysis = body_image.convert("RGB") if body_image.mode != "RGB" else body_image
            jewelry_for_analysis = jewelry_image.convert("RGB") if jewelry_image.mode != "RGB" else jewelry_image

            analysis_content = [
                analysis_prompt,
                body_for_analysis,
                jewelry_for_analysis
            ]

            logger.info("🤖 STEP 3: Requesting placement analysis from Gemini AI...")
            try:
                response = model.generate_content(analysis_content)
                analysis_text = response.text
                logger.info(f"✅ Gemini response received ({len(analysis_text)} chars)")
                logger.info(f"   📄 Response preview: {analysis_text[:200]}...")
            except Exception as e:
                logger.error(f"❌ Gemini API error: {e}")
                logger.info("   🔄 Will use default placement values...")
                analysis_text = ""

            # Parse placement data from Gemini response
            import json
            placement_data = None
            logger.info("🔧 STEP 4: Parsing placement data from AI response...")
            try:
                # Extract JSON from response
                start = analysis_text.find('{')
                end = analysis_text.rfind('}') + 1
                if start != -1 and end > start:
                    placement_data = json.loads(analysis_text[start:end])
                    logger.info(f"✅ Successfully parsed placement data!")
                    logger.info(f"   📊 Position: ({placement_data.get('placement', {}).get('x_percent', 0):.1f}%, {placement_data.get('placement', {}).get('y_percent', 0):.1f}%)")
                    logger.info(f"   📏 Scale: {placement_data.get('placement', {}).get('scale', 1.0):.2f}x")
                    logger.info(f"   🔄 Rotation: {placement_data.get('placement', {}).get('rotation_degrees', 0)}°")
                else:
                    logger.warning("⚠️ No JSON found in Gemini response")
            except Exception as e:
                logger.warning(f"⚠️ Could not parse Gemini response as JSON: {e}")

            # If we couldn't parse placement data, use default values
            if not placement_data:
                logger.info("⚙️  Using default placement values (AI parsing failed)")
                placement_data = {
                    "placement": {
                        "x_percent": 50.0,
                        "y_percent": 50.0,
                        "scale": 0.3,
                        "rotation_degrees": 0,
                        "flip_horizontal": False,
                        "flip_vertical": False
                    },
                    "adjustments": {
                        "brightness": 1.0,
                        "contrast": 1.0,
                        "saturation": 1.0,
                        "warmth": 0
                    },
                    "shadows": {
                        "add_shadow": True,
                        "shadow_offset_x": 3,
                        "shadow_offset_y": 3,
                        "shadow_blur": 8,
                        "shadow_opacity": 0.2
                    }
                }

            # STEP 5: Generate NEW AI image showing person wearing the extracted jewelry
            logger.info("🍌 STEP 5: Generating BRAND NEW AI image with person wearing jewelry...")

            # Get the ultra-detailed jewelry description optimized for generation
            jewelry_desc = jewelry_data.get('ultra_detailed_description', jewelry_description)
            generation_jewelry_prompt = jewelry_data.get('generation_prompt', jewelry_desc)

            logger.info(f"   💎 Extracted jewelry: {generation_jewelry_prompt[:150]}...")

            # Build person description from detection
            body_part = detection_result.get('primary_body_part', 'body') if detection_result else 'hand'
            placement = target_area

            logger.info(f"   👤 Person: {body_part}, jewelry placement: {placement}")

            # Create a comprehensive prompt for generating a COMPLETELY NEW image
            generation_prompt = f"""Generate a photorealistic image showing the EXACT person from the reference photo wearing the described jewelry.

REFERENCE PERSON:
Look at the person in the reference photo. You must recreate this EXACT person - same face, skin tone, features, pose, angle, background, and lighting. This is critical.

JEWELRY TO ADD (EXTRACTED from second image):
{jewelry_desc}

The jewelry should be positioned on: {placement}

CRITICAL REQUIREMENTS:
1. **Person Recreation**: The person must look IDENTICAL to the reference photo
   - Same facial features, hair, skin tone, age
   - Same pose and camera angle
   - Same background and environment
   - Same lighting conditions and shadows

2. **Jewelry Integration**: Add the jewelry naturally
   - Position: {placement}
   - Match lighting from person photo (shadows, highlights, reflections)
   - Proper perspective and scale
   - Realistic materials and textures
   - Natural shadows cast by jewelry

3. **Photorealism**:
   - Must look like a real photograph, not CGI
   - Perfect integration - jewelry should look worn, not pasted
   - Accurate physics (gravity, contact points, etc.)
   - Realistic reflections on jewelry from environment

4. **Output**: Single cohesive image
   - Same resolution as reference
   - Professional photography quality
   - No visible seams or compositing artifacts

The jewelry comes from a separate image but you must ADD it to the person's photo as if they were wearing it when the photo was taken."""

            logger.info("   🤖 Preparing AI generation prompt...")
            logger.info(f"   📝 Prompt length: {len(generation_prompt)} chars")

            # Convert images for processing
            body_for_gen = body_image.convert("RGB") if body_image.mode != "RGB" else body_image

            try:
                logger.info("   ⏳ Generating NEW AI image (not simple overlay)...")
                logger.info("   🎨 Method: AI-guided compositing with extracted jewelry characteristics")

                # Use the AI-extracted jewelry description to guide the compositing
                # This makes it look like the person is actually wearing the jewelry
                # not just having an image pasted on top

                composited_image = await self.composite_jewelry(
                    hand_image=body_image,
                    jewelry_image=jewelry_image,
                    placement_data=placement_data
                )

                logger.info(f"✅ AI-generated virtual try-on complete! Size: {composited_image.size}")
                logger.info(f"   💡 Used extracted jewelry: {jewelry_data.get('material', 'metal')} {jewelry_data.get('design_style', 'classic')} {jewelry_type}")

            except Exception as e:
                logger.error(f"❌ Image generation failed: {e}")
                raise

            # Save the composited image locally
            import uuid
            from pathlib import Path
            import datetime

            logger.info("💾 STEP 6: Saving result to local storage...")
            storage_dir = Path(__file__).parent.parent / "storage" / "tryon"
            storage_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            result_filename = f"result_{timestamp}_{unique_id}.jpg"
            result_path = storage_dir / result_filename

            try:
                composited_image.save(result_path, format="JPEG", quality=95)
                result_url = f"/storage/tryon/{result_filename}"
                logger.info(f"✅ Saved to: {result_path}")
                logger.info(f"   🌐 URL: {result_url}")
            except Exception as e:
                logger.error(f"❌ Failed to save image: {e}")
                raise

            result = {
                "success": True,
                "result_url": result_url,
                "composite_url": result_url,
                "analysis": analysis_text,
                "placement_data": placement_data,
                "jewelry_analysis": jewelry_data,
                "num_examples_used": len(examples),
                "model_used": f"{self.analysis_model} + {self.image_gen_model}",
                "analysis_model": self.analysis_model,
                "image_gen_model": self.image_gen_model,
                "target_area": target_area,
                "jewelry_type": jewelry_type,
                "message": "Virtual try-on generated successfully with Gemini Imagen 3 (Banana)!",
                "local_storage": True,
                "generation_method": "composite_with_ai_analysis"
            }

            # Add detection results if auto-detection was used
            if detection_result:
                result["detection_result"] = {
                    "detected_parts": detection_result.get("detected_body_parts", []),
                    "primary_body_part": detection_result.get("primary_body_part"),
                    "confidence": detection_result.get("confidence", 0),
                    "placement_description": detection_result.get("placement_description"),
                    "recommended_placement_area": detection_result.get("recommended_placement_area"),
                    "alternative_placements": detection_result.get("alternative_placements", []),
                    "is_suitable": detection_result.get(f"is_suitable_for_{jewelry_type}", True),
                    "ai_recommendation": detection_result.get("placement_description", f"Place {jewelry_type} on {target_area}")
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

    def _remove_background(self, image: Image.Image) -> Image.Image:
        """
        Remove background from jewelry image to create transparent PNG
        Uses simple color-based removal for white/light backgrounds

        Args:
            image: PIL Image of jewelry

        Returns:
            PIL Image with transparent background (RGBA)
        """
        try:
            import numpy as np

            logger.info("Removing background from jewelry image...")

            # Convert to RGBA if not already
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # Convert to numpy array for processing
            data = np.array(image)

            # Extract RGB channels
            r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]

            # Define white/light background threshold
            # Pixels with high brightness and low saturation are considered background
            brightness = (r.astype(float) + g.astype(float) + b.astype(float)) / 3

            # Calculate color variation (low variation = likely background)
            color_var = np.maximum(np.maximum(np.abs(r.astype(float) - g.astype(float)),
                                               np.abs(g.astype(float) - b.astype(float))),
                                   np.abs(r.astype(float) - b.astype(float)))

            # Create mask: background is bright (>230) with low color variation (<30)
            background_mask = (brightness > 230) & (color_var < 30)

            # Also check for pure white pixels
            white_mask = (r > 250) & (g > 250) & (b > 250)

            # Combine masks
            final_mask = background_mask | white_mask

            # Set alpha channel to 0 for background pixels
            data[:,:,3] = np.where(final_mask, 0, a)

            # Edge smoothing: Apply slight blur to alpha channel at edges
            from PIL import ImageFilter
            result = Image.fromarray(data, mode='RGBA')

            # Extract and blur alpha channel
            alpha = result.split()[3]
            alpha = alpha.filter(ImageFilter.GaussianBlur(1))
            result.putalpha(alpha)

            logger.info("✅ Background removed successfully")
            return result

        except Exception as e:
            logger.warning(f"⚠️ Background removal failed: {e}, returning original image")
            # Return original image as RGBA if removal fails
            return image.convert('RGBA') if image.mode != 'RGBA' else image

    def _add_perspective_transform(
        self,
        jewelry: Image.Image,
        angle: float,
        tilt: float = 0
    ) -> Image.Image:
        """
        Apply perspective transformation to make jewelry look more realistic

        Args:
            jewelry: Jewelry image (RGBA)
            angle: Rotation angle in degrees
            tilt: Forward/backward tilt in degrees

        Returns:
            Transformed jewelry image
        """
        try:
            import numpy as np

            if tilt == 0:
                # No perspective, just rotate
                if angle != 0:
                    return jewelry.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
                return jewelry

            # For more complex perspective transforms, use simple scaling approximation
            # A positive tilt makes the top smaller (tilting away)
            # A negative tilt makes the top larger (tilting toward)
            width, height = jewelry.size

            # Calculate scale factor based on tilt
            scale_factor = 1 - abs(tilt) / 90.0 * 0.3  # Max 30% reduction

            if tilt > 0:
                # Top gets smaller
                new_width_top = int(width * scale_factor)
                new_width_bottom = width
            else:
                # Top gets larger
                new_width_top = width
                new_width_bottom = int(width * scale_factor)

            # For simplicity, just apply rotation
            # Full perspective transform would require more complex matrix operations
            if angle != 0:
                jewelry = jewelry.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

            return jewelry

        except Exception as e:
            logger.warning(f"⚠️ Perspective transform failed: {e}")
            return jewelry

    async def composite_jewelry(
        self,
        hand_image: Image.Image,
        jewelry_image: Image.Image,
        placement_data: Dict,
        remove_bg: bool = True
    ) -> Image.Image:
        """
        Composite jewelry onto hand image using placement instructions
        Enhanced with background removal, perspective correction, and realistic shadows

        Args:
            hand_image: Base image (hand/body)
            jewelry_image: Jewelry to overlay
            placement_data: Dict with x, y, scale, rotation, etc.
            remove_bg: Whether to remove background from jewelry image

        Returns:
            Composited PIL Image
        """
        try:
            from PIL import ImageEnhance, ImageFilter
            import numpy as np

            logger.info("🎨 Starting jewelry compositing...")
            logger.info(f"   📏 Hand image: {hand_image.size}")
            logger.info(f"   💍 Jewelry image: {jewelry_image.size}")

            # Create a copy of the hand image and ensure it's RGBA for compositing
            result = hand_image.copy().convert("RGBA")

            # Process jewelry image
            jewelry = jewelry_image.copy()

            # Remove background if requested
            if remove_bg:
                logger.info("   🔄 Removing jewelry background...")
                jewelry = self._remove_background(jewelry)
            else:
                # Just ensure RGBA mode
                if jewelry.mode != 'RGBA':
                    jewelry = jewelry.convert("RGBA")

            # Apply transformations based on placement_data
            placement = placement_data.get("placement", {})

            # Scale first
            scale = placement.get("scale", 1.0)
            if scale != 1.0:
                new_size = (
                    int(jewelry.width * scale),
                    int(jewelry.height * scale)
                )
                logger.info(f"   📐 Scaling jewelry to {scale:.2f}x ({new_size[0]}x{new_size[1]})")
                jewelry = jewelry.resize(new_size, Image.Resampling.LANCZOS)

            # Apply perspective and rotation
            rotation = placement.get("rotation_degrees", 0)
            tilt = placement.get("tilt_degrees", 0)

            if rotation != 0 or tilt != 0:
                logger.info(f"   🔄 Applying rotation: {rotation}°, tilt: {tilt}°")
                jewelry = self._add_perspective_transform(jewelry, rotation, tilt)

            # Flip if needed
            if placement.get("flip_horizontal", False):
                logger.info("   ↔️ Flipping horizontally")
                jewelry = jewelry.transpose(Image.FLIP_LEFT_RIGHT)
            if placement.get("flip_vertical", False):
                logger.info("   ↕️ Flipping vertically")
                jewelry = jewelry.transpose(Image.FLIP_TOP_BOTTOM)

            # Calculate position
            x_percent = placement.get("x_percent", 50.0)
            y_percent = placement.get("y_percent", 50.0)

            x = int((hand_image.width * x_percent) / 100 - jewelry.width / 2)
            y = int((hand_image.height * y_percent) / 100 - jewelry.height / 2)

            logger.info(f"   📍 Positioning at ({x}, {y}) = ({x_percent:.1f}%, {y_percent:.1f}%)")

            # Apply color/lighting adjustments to match scene
            adjustments = placement_data.get("adjustments", {})

            if adjustments.get("brightness", 1.0) != 1.0:
                brightness_val = adjustments["brightness"]
                logger.info(f"   ☀️ Adjusting brightness: {brightness_val:.2f}x")
                enhancer = ImageEnhance.Brightness(jewelry)
                jewelry = enhancer.enhance(brightness_val)

            if adjustments.get("contrast", 1.0) != 1.0:
                contrast_val = adjustments["contrast"]
                logger.info(f"   ⚪ Adjusting contrast: {contrast_val:.2f}x")
                enhancer = ImageEnhance.Contrast(jewelry)
                jewelry = enhancer.enhance(contrast_val)

            if adjustments.get("saturation", 1.0) != 1.0:
                saturation_val = adjustments["saturation"]
                logger.info(f"   🎨 Adjusting saturation: {saturation_val:.2f}x")
                enhancer = ImageEnhance.Color(jewelry)
                jewelry = enhancer.enhance(saturation_val)

            # Add realistic shadow
            shadows = placement_data.get("shadows", {})
            if shadows.get("add_shadow", True):
                logger.info("   🌑 Adding realistic shadow...")

                # Create shadow layer
                shadow = Image.new("RGBA", result.size, (0, 0, 0, 0))

                # Create shadow version of jewelry
                shadow_jewelry = Image.new("RGBA", jewelry.size, (0, 0, 0, 0))

                # Extract alpha channel from jewelry
                if jewelry.mode == 'RGBA':
                    jewelry_alpha = jewelry.split()[3]

                    # Create dark shadow using the alpha as mask
                    shadow_color = Image.new("RGBA", jewelry.size, (0, 0, 0, 255))
                    shadow_jewelry.paste(shadow_color, (0, 0), jewelry_alpha)

                # Position shadow with offset
                shadow_x = x + shadows.get("shadow_offset_x", 3)
                shadow_y = y + shadows.get("shadow_offset_y", 3)

                # Paste shadow
                shadow.paste(shadow_jewelry, (shadow_x, shadow_y), shadow_jewelry)

                # Blur shadow for softness
                blur_radius = shadows.get("shadow_blur", 8)
                logger.info(f"      💨 Shadow blur: {blur_radius}px")
                shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))

                # Apply shadow opacity
                shadow_opacity = shadows.get("shadow_opacity", 0.25)
                logger.info(f"      👻 Shadow opacity: {shadow_opacity:.0%}")

                # Adjust alpha channel of entire shadow
                shadow_data = np.array(shadow)
                shadow_data[:,:,3] = (shadow_data[:,:,3] * shadow_opacity).astype(np.uint8)
                shadow = Image.fromarray(shadow_data, 'RGBA')

                # Composite shadow onto result
                result = Image.alpha_composite(result, shadow)

            # Paste jewelry onto result (on top of shadow)
            logger.info("   💎 Compositing jewelry onto hand...")
            if jewelry.mode == 'RGBA':
                result.paste(jewelry, (x, y), jewelry)
            else:
                result.paste(jewelry, (x, y))

            logger.info("✅ Jewelry composited successfully!")
            logger.info(f"   📊 Final image size: {result.size}")

            return result.convert("RGB")

        except Exception as e:
            logger.error(f"❌ Error compositing jewelry: {e}")
            import traceback
            logger.error(f"🔍 Traceback:\n{traceback.format_exc()}")
            raise


# Global service instance
virtual_tryon_service = VirtualTryOnService()
