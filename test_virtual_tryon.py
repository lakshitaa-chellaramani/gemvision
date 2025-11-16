"""
Test script for Virtual Try-On Service
Tests the AI-powered virtual try-on using Gemini 2.5 Flash Image Preview
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from PIL import Image, ImageDraw
from backend.services.virtual_tryon_service import virtual_tryon_service
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_person_image() -> Image.Image:
    """Create a simple test person image"""
    img = Image.new('RGB', (512, 512), color='#F0E5DE')
    draw = ImageDraw.Draw(img)

    # Draw a simple hand shape
    draw.ellipse([150, 200, 350, 400], fill='#FFE0BD', outline='#D4A574', width=2)

    # Draw fingers
    for i, x in enumerate([180, 230, 260, 290, 330]):
        draw.ellipse([x-15, 150, x+15, 220], fill='#FFE0BD', outline='#D4A574', width=2)

    # Add text
    draw.text((150, 450), "Test Hand Image", fill='#333')

    return img


def create_test_jewelry_image() -> Image.Image:
    """Create a simple test jewelry image (ring)"""
    img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a gold ring
    # Outer circle
    draw.ellipse([50, 100, 206, 200], fill='#FFD700', outline='#DAA520', width=3)

    # Inner circle (hole)
    draw.ellipse([80, 120, 176, 180], fill=(0, 0, 0, 0), outline='#B8860B', width=2)

    # Add a small diamond
    draw.polygon([(128, 80), (115, 100), (128, 90), (141, 100)], fill='#E0FFFF', outline='#87CEEB')

    return img


async def test_virtual_tryon():
    """Test the virtual try-on service"""
    try:
        logger.info("=" * 80)
        logger.info("TESTING VIRTUAL TRY-ON SERVICE")
        logger.info("=" * 80)

        # Create test images
        logger.info("Creating test images...")
        person_image = create_test_person_image()
        jewelry_image = create_test_jewelry_image()

        # Save test images for reference
        test_dir = Path(__file__).parent / "backend" / "storage" / "test"
        test_dir.mkdir(parents=True, exist_ok=True)

        person_path = test_dir / "test_person.png"
        jewelry_path = test_dir / "test_jewelry.png"

        person_image.save(person_path)
        jewelry_image.save(jewelry_path)

        logger.info(f"Test images saved:")
        logger.info(f"  Person: {person_path}")
        logger.info(f"  Jewelry: {jewelry_path}")

        # Test the virtual try-on service
        logger.info("\nGenerating virtual try-on...")
        result = await virtual_tryon_service.generate_tryon_image(
            person_image=person_image,
            jewelry_image=jewelry_image,
            jewelry_type="ring",
            jewelry_description="A beautiful gold ring with a small diamond"
        )

        logger.info("\n" + "=" * 80)
        logger.info("RESULT:")
        logger.info("=" * 80)
        logger.info(f"Success: {result['success']}")
        logger.info(f"Result URL: {result['result_url']}")
        logger.info(f"Local Path: {result['local_path']}")
        logger.info(f"Model Used: {result['model_used']}")
        logger.info(f"Generation Method: {result['generation_method']}")
        logger.info(f"Image Size: {result['image_size']}")
        logger.info(f"File Size: {result['size']} bytes")

        if result.get('s3_url'):
            logger.info(f"S3 URL: {result['s3_url']}")

        logger.info("\n" + "=" * 80)
        logger.info("TEST COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)

        return result

    except Exception as e:
        logger.error("=" * 80)
        logger.error("TEST FAILED!")
        logger.error(f"Error: {e}")
        logger.error("=" * 80)
        import traceback
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    # Run the test
    result = asyncio.run(test_virtual_tryon())

    print("\n\n")
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Generated image saved to: {result['local_path']}")
    print(f"You can view it at: {result['result_url']}")
    print("=" * 80)
