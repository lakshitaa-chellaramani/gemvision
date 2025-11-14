"""
Demo Data Generator for GemVision
Generates sample designs, try-ons, and inspections for testing
"""
from backend.models.database import SessionLocal, Design, User, TryOn, QCInspection
from datetime import datetime, timedelta
import random


def create_demo_user():
    """Create a demo user"""
    db = SessionLocal()

    # Check if user exists
    user = db.query(User).filter(User.id == 1).first()
    if user:
        print("Demo user already exists")
        return user

    # Create user
    user = User(
        id=1,
        email="demo@gemvision.com",
        username="demo",
        created_at=datetime.utcnow()
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    print(f"Created demo user: {user.username}")
    return user


def create_demo_designs():
    """Create sample designs"""
    db = SessionLocal()

    sample_designs = [
        {
            "category": "ring",
            "style_preset": "bridal",
            "prompt": "Elegant solitaire engagement ring with round brilliant diamond, platinum band",
            "realism_mode": "realistic",
            "materials": ["platinum", "diamond"],
            "colors": ["silver", "white"]
        },
        {
            "category": "necklace",
            "style_preset": "minimalist",
            "prompt": "Simple diamond pendant necklace with delicate chain, modern design",
            "realism_mode": "realistic",
            "materials": ["gold", "diamond"],
            "colors": ["gold", "white"]
        },
        {
            "category": "earring",
            "style_preset": "traditional",
            "prompt": "Traditional gold stud earrings with filigree work and small rubies",
            "realism_mode": "realistic",
            "materials": ["gold", "ruby"],
            "colors": ["gold", "red"]
        },
        {
            "category": "bracelet",
            "style_preset": "heavy-stone",
            "prompt": "Bold statement bracelet with large emeralds and diamond accents",
            "realism_mode": "realistic",
            "materials": ["gold", "emerald", "diamond"],
            "colors": ["gold", "green", "white"]
        },
        {
            "category": "ring",
            "style_preset": "antique",
            "prompt": "Vintage art deco ring with emerald cut diamond and milgrain details",
            "realism_mode": "realistic",
            "materials": ["white gold", "diamond"],
            "colors": ["silver", "white"]
        }
    ]

    for i, design_data in enumerate(sample_designs):
        # Check if already exists
        existing = db.query(Design).filter(
            Design.prompt == design_data["prompt"]
        ).first()

        if existing:
            continue

        design = Design(
            user_id=1,
            category=design_data["category"],
            style_preset=design_data["style_preset"],
            prompt=design_data["prompt"],
            realism_mode=design_data["realism_mode"],
            generated_images=["https://via.placeholder.com/1024"],  # Placeholder
            seed_id=f"demo_seed_{i}",
            model_version="dall-e-3",
            generation_id=f"demo_gen_{i}",
            dominant_materials=design_data["materials"],
            dominant_colors=design_data["colors"],
            confidence_score=random.uniform(0.75, 0.95),
            is_idea=random.choice([True, False]),
            is_favorite=random.choice([True, False]),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )

        db.add(design)

    db.commit()
    print(f"Created {len(sample_designs)} demo designs")


def create_demo_data():
    """Create all demo data"""
    print("Creating demo data for GemVision...")

    # Create user
    create_demo_user()

    # Create designs
    create_demo_designs()

    print("\nDemo data created successfully!")
    print("You can now test the application with sample data.")


if __name__ == "__main__":
    create_demo_data()
