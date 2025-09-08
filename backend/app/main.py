"""FastAPI application for RecallGuard."""

import os
import logging
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.core.database import get_db
from app.core.models import User, Product, RecallAlert, Recall
from app.core.schemas import UserCreate, User as UserSchema, UserWithProducts, Product as ProductSchema, ProductCreate
from app.core.crud import create_user, get_user, list_products
from app.services.background_jobs import start_background_jobs, stop_background_jobs, run_manual_recall_check
from app.services.recall_fetcher import recall_fetcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting RecallGuard API...")
    await start_background_jobs()
    logger.info("Background jobs started")

    yield

    # Shutdown
    logger.info("Shutting down RecallGuard API...")
    await stop_background_jobs()
    logger.info("Background jobs stopped")

# Load environment variables
load_dotenv()

app = FastAPI(
    title="RecallGuard API",
    description="Backend API for RecallGuard - Product recall alert system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/users", response_model=UserWithProducts, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)) -> UserWithProducts:
    """Create a new user with optional initial products."""
    try:
        db_user = create_user(db, user)
        return UserWithProducts.model_validate(db_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}"
        )


@app.get("/users/{user_id}", response_model=UserSchema)
async def get_user_endpoint(user_id: int, db: Session = Depends(get_db)) -> UserSchema:
    """Get a user by ID."""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserSchema.model_validate(db_user)


@app.get("/users/{user_id}/products", response_model=List[ProductSchema])
async def get_user_products(user_id: int, db: Session = Depends(get_db)) -> List[ProductSchema]:
    """Get all products for a specific user."""
    # First check if user exists
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    products = list_products(db, user_id)
    return [ProductSchema.model_validate(product) for product in products]


@app.post("/users/{user_id}/products", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def add_product_to_user(user_id: int, product: ProductCreate, db: Session = Depends(get_db)) -> ProductSchema:
    """Add a new product to an existing user."""
    # First check if user exists
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    try:
        # Create the product
        db_product = Product(
            user_id=user_id,
            product_name=product.product_name,
            brand=product.brand,
            model=product.model
        )
        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        return ProductSchema.model_validate(db_product)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add product: {str(e)}"
        )


@app.post("/admin/manual-recall-check")
async def trigger_manual_recall_check() -> dict:
    """Trigger a manual recall check (admin endpoint)."""
    try:
        await run_manual_recall_check()
        return {"status": "success", "message": "Manual recall check triggered"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger recall check: {str(e)}"
        )


@app.post("/admin/scrape-recalls")
async def trigger_recall_scraping(days_back: int = 7) -> dict:
    """Trigger manual recall scraping (admin endpoint)."""
    try:
        stats = await recall_fetcher.fetch_and_store_recalls(days_back=days_back)
        return {
            "status": "success",
            "message": "Recall scraping completed",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape recalls: {str(e)}"
        )


@app.get("/users/{user_id}/recall-alerts")
async def get_user_recall_alerts(user_id: int, limit: int = 50, db: Session = Depends(get_db)) -> dict:
    """Get recall alerts for a specific user."""
    # Check if user exists
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    try:
        # Get user's recall alerts with related data
        alerts = db.query(RecallAlert).filter(
            RecallAlert.user_id == user_id
        ).order_by(RecallAlert.created_at.desc()).limit(limit).all()

        # Format alerts for response
        formatted_alerts = []
        for alert in alerts:
            # Get related recall and product data
            recall = db.query(Recall).filter(Recall.id == alert.recall_id).first()
            product = db.query(Product).filter(Product.id == alert.product_id).first()

            formatted_alerts.append({
                "id": alert.id,
                "match_score": alert.match_score,
                "confidence": alert.confidence,
                "created_at": alert.created_at.isoformat(),
                "notification_sent": alert.notification_sent,
                "recall": {
                    "id": recall.id if recall else None,
                    "source": recall.source if recall else None,
                    "product_name": recall.product_name if recall else None,
                    "brand": recall.brand if recall else None,
                    "recall_date": recall.recall_date.isoformat() if recall and recall.recall_date else None,
                    "details": recall.details if recall else None,
                    "link": recall.link if recall else None
                },
                "product": {
                    "id": product.id if product else None,
                    "product_name": product.product_name if product else None,
                    "brand": product.brand if product else None,
                    "model": product.model if product else None
                }
            })

        # Get summary stats
        total_alerts = db.query(RecallAlert).filter(RecallAlert.user_id == user_id).count()
        high_priority_alerts = db.query(RecallAlert).filter(
            RecallAlert.user_id == user_id,
            RecallAlert.confidence == 'high'
        ).count()

        # Get last check time (most recent alert creation)
        last_alert = db.query(RecallAlert).filter(
            RecallAlert.user_id == user_id
        ).order_by(RecallAlert.created_at.desc()).first()

        return {
            "user_id": user_id,
            "alerts": formatted_alerts,
            "total_alerts": total_alerts,
            "high_priority_alerts": high_priority_alerts,
            "last_check": last_alert.created_at.isoformat() if last_alert else None
        }

    except Exception as e:
        logger.error(f"Error getting recall alerts for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recall alerts: {str(e)}"
        )


@app.get("/recalls")
async def get_recalls(
    page: int = 1,
    per_page: int = 20,
    search: str = None,
    source: str = None,
    category: str = None,
    processed: bool = None,
    sort_by: str = "recall_date",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
) -> dict:
    """Get paginated recalls with filtering and search."""
    try:
        query = db.query(Recall)

        # Apply filters
        if processed is not None:
            query = query.filter(Recall.processed == processed)
        
        if source:
            query = query.filter(Recall.source == source)
        
        if category:
            query = query.filter(Recall.category == category)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Recall.product_name.ilike(search_term)) |
                (Recall.brand.ilike(search_term)) |
                (Recall.model.ilike(search_term)) |
                (Recall.details.ilike(search_term))
            )

        # Get total count before pagination
        total_count = query.count()

        # Apply sorting with validation
        valid_sort_fields = ['recall_date', 'created_at', 'product_name', 'brand', 'model']
        if sort_by not in valid_sort_fields:
            sort_by = 'recall_date'
        
        sort_column = getattr(Recall, sort_by, None)
        if sort_column is not None:
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(Recall.recall_date.desc())

        # Apply pagination
        offset = (page - 1) * per_page
        recalls = query.offset(offset).limit(per_page).all()

        formatted_recalls = []
        for recall in recalls:
            try:
                formatted_recalls.append({
                    "id": recall.id,
                    "source": recall.source or "Unknown",
                    "category": recall.category,
                    "product_name": recall.product_name or "Unknown Product",
                    "brand": recall.brand,
                    "model": recall.model,
                    "recall_date": recall.recall_date.isoformat() if recall.recall_date else None,
                    "details": recall.details,
                    "link": recall.link,
                    "processed": recall.processed if recall.processed is not None else False,
                    "created_at": recall.created_at.isoformat() if recall.created_at else None
                })
            except Exception as e:
                logger.error(f"Error formatting recall {recall.id}: {e}")
                continue

        # Get statistics
        try:
            sources_query = db.query(Recall.source).distinct().all()
            sources_list = [s[0] for s in sources_query if s[0]] if sources_query else []
            
            categories_query = db.query(Recall.category).distinct().all()
            categories_list = [c[0] for c in categories_query if c[0]] if categories_query else []
            
            stats = {
                "total_recalls": db.query(Recall).count(),
                "unprocessed_recalls": db.query(Recall).filter(Recall.processed == False).count(),
                "sources": sources_list,
                "categories": categories_list
            }
        except Exception as e:
            logger.warning(f"Error getting stats: {e}")
            stats = {
                "total_recalls": total_count,
                "unprocessed_recalls": 0,
                "sources": [],
                "categories": []
            }

        return {
            "recalls": formatted_recalls,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "pages": (total_count + per_page - 1) // per_page
            },
            "stats": stats,
            "filters": {
                "search": search,
                "source": source,
                "category": category,
                "processed": processed
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recalls: {str(e)}"
        )

@app.get("/recalls/{recall_id}")
async def get_recall_detail(recall_id: int, db: Session = Depends(get_db)) -> dict:
    """Get detailed information about a specific recall."""
    recall = db.query(Recall).filter(Recall.id == recall_id).first()
    
    if not recall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recall not found"
        )
    
    # Get any alerts related to this recall
    alerts = db.query(RecallAlert).filter(RecallAlert.recall_id == recall_id).all()
    
    return {
        "id": recall.id,
        "source": recall.source,
        "source_id": recall.source_id,
        "category": recall.category,
        "product_name": recall.product_name,
        "brand": recall.brand,
        "model": recall.model,
        "recall_date": recall.recall_date.isoformat() if recall.recall_date else None,
        "details": recall.details,
        "link": recall.link,
        "processed": recall.processed,
        "created_at": recall.created_at.isoformat(),
        "updated_at": recall.updated_at.isoformat() if recall.updated_at else None,
        "raw_data": recall.raw_data,
        "alerts_count": len(alerts),
        "affected_users": len(set(alert.user_id for alert in alerts))
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)) -> dict:
    """Health check endpoint."""
    # Get database stats
    try:
        total_users = db.query(User).count()
        total_products = db.query(Product).count()
        total_recalls = db.query(Recall).count()
        unprocessed_recalls = db.query(Recall).filter(Recall.processed == False).count()
        total_alerts = db.query(RecallAlert).count()
    except Exception as e:
        logger.error(f"Error getting health stats: {e}")
        total_users = total_products = total_recalls = unprocessed_recalls = total_alerts = -1

    return {
        "status": "healthy",
        "service": "RecallGuard API",
        "features": {
            "background_jobs": "enabled",
            "ai_matching": "enabled",
            "notifications": "enabled",
            "recall_sources": ["FDA", "CPSC"],
            "database_storage": "enabled"
        },
        "stats": {
            "users": total_users,
            "products": total_products,
            "recalls": total_recalls,
            "unprocessed_recalls": unprocessed_recalls,
            "alerts": total_alerts
        }
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)