"""Pydantic schemas for RecallGuard API."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

__all__ = [
    "ProductBase", "ProductCreate", "Product",
    "UserBase", "UserCreate", "User", "UserWithProducts"
]


# Product schemas
class ProductBase(BaseModel):
    """Base product schema."""
    product_name: str
    brand: Optional[str] = None
    model: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass


class Product(ProductBase):
    """Schema for reading a product."""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# User schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    products: Optional[List[ProductCreate]] = []


class User(UserBase):
    """Schema for reading a user."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithProducts(User):
    """Schema for reading a user with their products."""
    products: List[Product] = []

    class Config:
        from_attributes = True