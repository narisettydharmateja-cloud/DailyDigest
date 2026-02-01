"""FastAPI backend for DailyDigest subscription management."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import List

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session, sessionmaker

from dailydigest.config import get_config
from dailydigest.models.db import Subscription, Base, Digest
from dailydigest.services.database import build_engine

# Configure logging
log = structlog.get_logger("api.subscription")

# FastAPI app
app = FastAPI(title="DailyDigest API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
config = get_config()
engine = build_engine(config.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


# Pydantic models
class SubscriptionCreate(BaseModel):
    """Schema for creating a new subscription."""
    
    email: EmailStr
    categories: List[str]
    frequency: str = "daily"


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""
    
    id: int
    email: str
    categories: List[str]
    frequency: str
    created_at: datetime
    is_active: str
    
    class Config:
        from_attributes = True


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "DailyDigest API", "version": "1.0.0"}


@app.post("/api/subscribe", response_model=SubscriptionResponse)
def create_subscription(subscription: SubscriptionCreate):
    """Create a new subscription."""
    
    db: Session = SessionLocal()
    
    try:
        # Check if email already exists
        existing = db.query(Subscription).filter(Subscription.email == subscription.email).first()
        
        if existing:
            # Update existing subscription
            existing.categories = subscription.categories
            existing.frequency = subscription.frequency
            existing.updated_at = datetime.now(UTC)
            existing.is_active = "true"
            db.commit()
            db.refresh(existing)
            
            log.info("subscription_updated", email=subscription.email)
            return existing
        
        # Create new subscription
        db_subscription = Subscription(
            email=subscription.email,
            categories=subscription.categories,
            frequency=subscription.frequency
        )
        
        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)
        
        log.info("subscription_created", email=subscription.email, categories=subscription.categories)
        
        return db_subscription
        
    except Exception as e:
        db.rollback()
        log.error("subscription_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        db.close()


@app.get("/api/subscriptions", response_model=List[SubscriptionResponse])
def list_subscriptions():
    """List all active subscriptions."""
    
    db: Session = SessionLocal()
    
    try:
        subscriptions = db.query(Subscription).filter(Subscription.is_active == "true").all()
        return subscriptions
    
    finally:
        db.close()


@app.delete("/api/subscribe/{email}")
def unsubscribe(email: str):
    """Unsubscribe an email address."""
    
    db: Session = SessionLocal()
    
    try:
        subscription = db.query(Subscription).filter(Subscription.email == email).first()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        subscription.is_active = "false"
        subscription.updated_at = datetime.now(UTC)
        db.commit()
        
        log.info("unsubscribed", email=email)
        
        return {"message": "Successfully unsubscribed"}
    
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
