"""
Database models and setup for GemVision
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from backend.app.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    designs = relationship("Design", back_populates="user")
    tryons = relationship("TryOn", back_populates="user")
    qc_inspections = relationship("QCInspection", back_populates="user")


class Design(Base):
    """AI-generated jewellery design model"""
    __tablename__ = "designs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Design metadata
    category = Column(String, index=True)  # Ring, Necklace, Earring, Bracelet
    style_preset = Column(String, index=True)  # Bridal, Minimalist, Traditional, etc.
    prompt = Column(Text)
    realism_mode = Column(String)  # Realistic, Sketch, CAD, etc.

    # Generation details
    generated_images = Column(JSON)  # List of image URLs
    seed_id = Column(String)
    model_version = Column(String)
    generation_id = Column(String, unique=True, index=True)

    # Auto-detected attributes
    dominant_materials = Column(JSON)  # ["gold", "diamond"]
    dominant_colors = Column(JSON)  # ["gold", "white"]
    confidence_score = Column(Float)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    is_favorite = Column(Boolean, default=False)
    is_idea = Column(Boolean, default=False)  # Saved as "Idea"

    # Status
    status = Column(String, default="generated")  # generated, approved, in_production, etc.

    # Relationships
    user = relationship("User", back_populates="designs")
    tryons = relationship("TryOn", back_populates="design")


class TryOn(Base):
    """Virtual try-on session model"""
    __tablename__ = "tryons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    design_id = Column(Integer, ForeignKey("designs.id"), nullable=True)

    # Hand photo
    hand_photo_url = Column(String)

    # Overlay details
    overlay_image_url = Column(String)
    overlay_transform = Column(JSON)  # {x, y, scale, rotation, opacity, hue}

    # Finger positioning
    finger_type = Column(String)  # Index, Middle, Ring, Little
    anchor_points = Column(JSON)  # {knuckle: {x, y}, base: {x, y}}

    # Snapshot
    snapshot_url = Column(String)
    snapshot_filename = Column(String)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    is_approved = Column(Boolean, default=False)
    sent_for_approval = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="tryons")
    design = relationship("Design", back_populates="tryons")


class QCInspection(Base):
    """Quality control inspection model"""
    __tablename__ = "qc_inspections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Inspected item
    item_image_url = Column(String)
    item_thumbnail_url = Column(String)
    item_reference = Column(String)  # Design ID, Order ID, etc.

    # Detection results
    detections = Column(JSON)  # [{x, y, w, h, label, confidence, severity}]
    detection_mode = Column(String)  # simulated or ml
    model_version = Column(String)

    # Operator decision
    operator_decision = Column(String)  # accept, rework, escalate
    operator_notes = Column(Text)
    is_false_positive = Column(Boolean, default=False)

    # Rework details
    rework_job_id = Column(Integer, ForeignKey("rework_jobs.id"), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    inspected_at = Column(DateTime)
    confidence_threshold = Column(Float)

    # Relationships
    user = relationship("User", back_populates="qc_inspections")
    rework_job = relationship("ReworkJob", back_populates="inspection")


class ReworkJob(Base):
    """Rework job model for defect remediation"""
    __tablename__ = "rework_jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Defect details
    defect_type = Column(String)
    defect_severity = Column(String)  # Low, Medium, High
    defect_description = Column(Text)

    # Evidence
    evidence_images = Column(JSON)  # List of image URLs

    # Assignment
    assigned_to_station = Column(String)
    priority = Column(String)  # Low, Medium, High, Critical

    # Status tracking
    status = Column(String, default="pending")  # pending, in_progress, completed, verified
    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime)
    completed_at = Column(DateTime)
    verified_at = Column(DateTime)

    # Assigned operators
    assigned_operator = Column(String)
    verified_by = Column(String)

    # Audit trail
    lifecycle_events = Column(JSON)  # [{timestamp, status, operator, notes}]

    # Relationships
    inspection = relationship("QCInspection", back_populates="rework_job")


class Analytics(Base):
    """Analytics and logging model"""
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Event details
    event_type = Column(String, index=True)  # generation, tryon, qc, etc.
    event_action = Column(String)  # created, viewed, approved, etc.
    event_data = Column(JSON)

    # Session
    session_id = Column(String, index=True)
    ip_address = Column(String)
    user_agent = Column(String)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Integer)  # Event duration if applicable


# Create all tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
