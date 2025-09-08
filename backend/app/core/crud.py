"""CRUD operations for RecallGuard."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.models import User, Product
from app.core.schemas import UserCreate, ProductCreate

__all__ = ["create_user", "get_user", "list_products"]


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user with optional initial products."""
    db_user = User(
        email=user.email,
        phone=user.phone
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Add initial products if provided
    if user.products:
        for product_data in user.products:
            db_product = Product(
                user_id=db_user.id,
                product_name=product_data.product_name,
                brand=product_data.brand,
                model=product_data.model
            )
            db.add(db_product)
        db.commit()
        db.refresh(db_user)

    return db_user


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def list_products(db: Session, user_id: int) -> List[Product]:
    """List all products for a specific user."""
    return db.query(Product).filter(Product.user_id == user_id).all()