# File: app/api/routes/documents.py
"""Document CRUD routes"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.models import DocumentInput, Document, NodeUpdate
from app.controllers.document_controller import DocumentController
from app.api.dependencies import get_neo4j_repository, get_vector_repository
from app.repositories.neo4j_repository import Neo4jRepository
from app.repositories.vector_repository import VectorRepository
from app.core.exceptions import BaseAPIException, IngestionError
import logging

router = APIRouter(prefix="/nodes", tags=["documents"])
logger = logging.getLogger(__name__)


def get_document_controller(
    neo4j_repo: Neo4jRepository = Depends(get_neo4j_repository),
    vector_repo: VectorRepository = Depends(get_vector_repository)
) -> DocumentController:
    """Dependency to get document controller"""
    return DocumentController(neo4j_repo, vector_repo)


@router.post("", response_model=Document)
def create_document(
    doc_input: DocumentInput,
    controller: DocumentController = Depends(get_document_controller)
):
    """
    Ingest a new document
    
    - Cleans text
    - Generates embeddings
    - Stores in Neo4j and FAISS
    - Creates semantic relationships
    - Extracts entities
    """
    try:
        return controller.create_document(doc_input)
    except BaseAPIException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_document: {str(e)}", exc_info=True)
        raise IngestionError(f"Unexpected error: {str(e)}")


@router.get("/{node_id}")
def get_document(
    node_id: str,
    controller: DocumentController = Depends(get_document_controller)
) -> Dict[str, Any]:
    """Retrieve a document by ID"""
    return controller.get_document(node_id)


@router.put("/{node_id}")
def update_document(
    node_id: str,
    update_data: NodeUpdate,
    controller: DocumentController = Depends(get_document_controller)
) -> Dict[str, Any]:
    """
    Update a document
    
    - Optional: Update text/title/metadata
    - Optional: Regenerate embeddings and relationships
    """
    return controller.update_document(node_id, update_data)


@router.delete("/{node_id}")
def delete_document(
    node_id: str,
    controller: DocumentController = Depends(get_document_controller)
) -> Dict[str, str]:
    """Delete a document"""
    controller.delete_document(node_id)
    return {"status": "deleted", "id": node_id}
