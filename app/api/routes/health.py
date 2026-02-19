# File: app/api/routes/health.py
"""Health check routes"""
from fastapi import APIRouter
from app.database import neo4j_driver
from app.core.exceptions import DatabaseConnectionError
import logging

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/")
def root():
    """Root endpoint"""
    return {"message": "Hybrid Vector-Graph Retrieval API"}


@router.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        neo4j_driver.get_driver()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise DatabaseConnectionError(str(e))
