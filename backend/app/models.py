from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, PyEnum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sleep_records = relationship("SleepRecord", back_populates="user", cascade="all, delete-orphan")
    activity_records = relationship("ActivityRecord", back_populates="user", cascade="all, delete-orphan")
    health_metrics = relationship("HealthMetric", back_populates="user", cascade="all, delete-orphan")
    lifestyle_factors = relationship("LifestyleFactor", back_populates="user", cascade="all, delete-orphan")
    cluster_assignments = relationship("ClusterAssignment", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    uploads = relationship("DataUpload", back_populates="user", cascade="all, delete-orphan")


class SleepRecord(Base):
    __tablename__ = "sleep_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    total_sleep_minutes = Column(Float)
    deep_sleep_minutes = Column(Float)
    light_sleep_minutes = Column(Float)
    rem_sleep_minutes = Column(Float)
    awake_minutes = Column(Float)
    sleep_efficiency = Column(Float)
    sleep_score = Column(Float)
    bedtime = Column(DateTime)
    wake_time = Column(DateTime)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sleep_records")


class ActivityRecord(Base):
    __tablename__ = "activity_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    steps = Column(Integer)
    calories_burned = Column(Float)
    active_minutes = Column(Float)
    sedentary_minutes = Column(Float)
    distance_km = Column(Float)
    heart_rate_avg = Column(Float)
    heart_rate_max = Column(Float)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activity_records")


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    resting_heart_rate = Column(Float)
    hrv = Column(Float)
    spo2 = Column(Float)
    respiratory_rate = Column(Float)
    stress_score = Column(Float)
    body_temperature = Column(Float)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="health_metrics")


class LifestyleFactor(Base):
    __tablename__ = "lifestyle_factors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    caffeine_mg = Column(Float, default=0)
    alcohol_units = Column(Float, default=0)
    exercise_minutes = Column(Float, default=0)
    screen_time_minutes = Column(Float, default=0)
    stress_level = Column(Float)
    mood_score = Column(Float)
    work_hours = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="lifestyle_factors")


class ClusterAssignment(Base):
    __tablename__ = "cluster_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    cluster_id = Column(Integer, nullable=False)
    cluster_label = Column(String(100))
    algorithm = Column(String(50))
    silhouette_score = Column(Float)
    features = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="cluster_assignments")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    model_type = Column(String(50))
    predicted_archetype = Column(String(100))
    confidence = Column(Float)
    feature_importance = Column(JSON)
    shap_values = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")


class DataUpload(Base):
    __tablename__ = "data_uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255))
    source_type = Column(String(50))
    records_imported = Column(Integer, default=0)
    quality_score = Column(Float)
    status = Column(String(50), default="pending")
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="uploads")
