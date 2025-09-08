"""SQLAlchemy models for RecallGuard."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

__all__ = ["User", "Product", "Recall", "RecallAlert"]


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with products
    products = relationship("Product", back_populates="user")
    recall_alerts = relationship("RecallAlert", back_populates="user")


class Product(Base):
    """Product model."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_name = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with user
    user = relationship("User", back_populates="products")


class Recall(Base):
    """Recall model for storing scraped recall data."""

    __tablename__ = "recalls"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False, index=True)  # FDA, CPSC, etc.
    source_id = Column(String, nullable=True, index=True)  # Original ID from source
    category = Column(String, nullable=True, index=True)  # food, drug, consumer_product
    product_name = Column(String, nullable=False, index=True)
    brand = Column(String, nullable=True, index=True)
    model = Column(String, nullable=True, index=True)
    recall_date = Column(DateTime, nullable=False, index=True)
    details = Column(Text, nullable=True)
    link = Column(String, nullable=True)
    raw_data = Column(JSON, nullable=True)  # Store original API response
    processed = Column(Boolean, default=False, index=True)  # Has this been processed for alerts?
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with alerts
    recall_alerts = relationship("RecallAlert", back_populates="recall")


class RecallAlert(Base):
    """Model to track recall alerts sent to users."""

    __tablename__ = "recall_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recall_id = Column(Integer, ForeignKey("recalls.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    match_score = Column(Integer, nullable=False)  # 0-100
    confidence = Column(String, nullable=False)  # high, medium, low
    match_details = Column(JSON, nullable=True)  # Store match reasoning
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="recall_alerts")
    recall = relationship("Recall", back_populates="recall_alerts")
    product = relationship("Product")