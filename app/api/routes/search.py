# File: app/api/routes/search.py
"""Search routes"""
from fastapi import APIRouter, Depends
from typing import List

from app.models import VectorSearchRequest, GraphSearchRequest, HybridSearchRequest, SearchResult, HybridSearchResponse
from app.controllers.search_controller import SearchController
from app.api.dependencies import get_neo4j_repository, get_vector_repository
from app.repositories.neo4j_repository import Neo4jRepository
from app.repositories.vector_repository import VectorRepository
import logging

router = APIRouter(prefix="/search", tags=["search"])
logger = logging.getLogger(__name__)


def get_search_controller(
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository),
    vector_repo: VectorRepository = Depends(get_vector_repository)
) -> SearchController:
    """Dependency to get search controller"""
    return SearchController(neo4j_repo, vector_repo)


@router.post("/vector", response_model=List[SearchResult])
def vector_search(
    request: VectorSearchRequest,
    controller: SearchController = Depends(get_search_controller)
):
    """
    Pure vector similarity search using FAISS
    
    - Encodes query text
    - Searches FAISS index
    - Returns top-k similar documents
    """
    return controller.vector_search(request.query_text, request.top_k)


@router.get("/graph")
def graph_search(
    request: GraphSearchRequest = Depends(),
    controller: SearchController = Depends(get_search_controller)
):
    """
    Pure graph traversal from a starting node
    
    - Traverses relationships up to specified depth
    - Returns nodes and edges
    """
    return controller.graph_search(request.start_id, request.depth, request.relationship_types)


@router.post("/hybrid", response_model=HybridSearchResponse)
def hybrid_search(
    request: HybridSearchRequest,
    controller: SearchController = Depends(get_search_controller)
):
    return controller.hybrid_search(
        query_text=request.query_text,
        vector_weight=request.vector_weight,
        graph_weight=request.graph_weight,
        top_k=request.top_k,
        graph_depth=request.graph_expand_depth,
        query_embedding=request.query_embedding
    )
