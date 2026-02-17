# File: app/api/routes/edges.py
"""Edge/relationship CRUD routes"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.models import EdgeInput
from app.controllers.edge_controller import EdgeController
from app.api.dependencies import get_neo4j_repository
from app.repositories.neo4j_repository import Neo4jRepository
import logging

router = APIRouter(prefix="/edges", tags=["edges"])
logger = logging.getLogger(__name__)


def get_edge_controller(
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository)
) -> EdgeController:
    """Dependency to get edge controller"""
    return EdgeController(neo4j_repo)


@router.post("")
def create_edge(
    edge_input: EdgeInput,
    controller: EdgeController = Depends(get_edge_controller)
):
    """
    Create a relationship between two nodes
    
    - Validates edge type against whitelist
    - Creates relationship in Neo4j
    """
    return controller.create_edge(edge_input)


@router.get("/{edge_id}")
def get_edge(
    edge_id: str,
    controller: EdgeController = Depends(get_edge_controller)
) -> Dict[str, Any]:
    """Retrieve an edge by ID"""
    return controller.get_edge(edge_id)
