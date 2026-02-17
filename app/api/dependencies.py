# File: app/api/dependencies.py
"""Dependency injection for FastAPI"""
from app.database import neo4j_driver, faiss_index
from app.repositories.neo4j_repository import Neo4jRepository
from app.repositories.vector_repository import VectorRepository


def get_neo4j_repository() -> Neo4jRepository:
    """Dependency to get Neo4j repository instance"""
    return Neo4jRepository(neo4j_driver)


def get_vector_repository() -> VectorRepository:
    """Dependency to get vector repository instance"""
    return VectorRepository(faiss_index)
