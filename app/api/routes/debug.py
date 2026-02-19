# File: app/api/routes/debug.py
"""Debug and inspection routes for development"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import logging

from app.api.dependencies import get_neo4j_repository, get_vector_repository
from app.repositories.neo4j_repository import Neo4jRepository
from app.repositories.vector_repository import VectorRepository

router = APIRouter(prefix="/debug", tags=["debug"])
logger = logging.getLogger(__name__)


@router.get("/documents")
def get_all_documents(neo4j_repo: Neo4jRepository = Depends(
        get_neo4j_repository)) -> List[Dict[str, Any]]:
    """Get all documents from Neo4j"""
    query = """
    MATCH (d:Document)
    RETURN d
    ORDER BY d.id
    """

    documents = []
    with neo4j_repo.driver.get_session() as session:
        result = session.run(query)
        for record in result:
            doc_dict = dict(record['d'])
            documents.append(doc_dict)

    return documents


@router.get("/entities")
def get_all_entities(neo4j_repo: Neo4jRepository = Depends(
        get_neo4j_repository)) -> List[Dict[str, Any]]:
    """Get all entities from Neo4j"""
    query = """
    MATCH (e:Entity)
    RETURN e
    ORDER BY e.name
    """

    entities = []
    with neo4j_repo.driver.get_session() as session:
        result = session.run(query)
        for record in result:
            ent_dict = dict(record['e'])
            entities.append(ent_dict)

    return entities


@router.get("/faiss/info")
def get_faiss_info(vector_repo: VectorRepository = Depends(
        get_vector_repository)) -> Dict[str, Any]:
    """Get FAISS index information"""
    try:
        # Access the FaissIndex wrapper attributes
        total_vectors = vector_repo.index.count()
        dimension = vector_repo.index.dimension

        # Get ID mapping
        id_map = {}
        for vector_id, doc_id in vector_repo.index.id_map.items():
            id_map[str(vector_id)] = doc_id

        return {
            "total_vectors": total_vectors,
            "dimension": dimension,
            "id_map": id_map,
            "is_trained": True  # FlatIP is always trained
        }
    except Exception as e:
        logger.error(f"Failed to get FAISS info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/faiss/vector/{vector_id}")
def get_vector_by_id(
    vector_id: int,
    vector_repo: VectorRepository = Depends(get_vector_repository)
) -> Dict[str, Any]:
    """Get a specific vector embedding by its ID"""
    try:
        embedding = vector_repo.get_vector(vector_id)

        if embedding is None:
            raise HTTPException(
                status_code=404,
                detail=f"Vector {vector_id} not found")

        doc_id = vector_repo.get_document_id(vector_id)

        return {
            "vector_id": vector_id,
            "document_id": doc_id,
            "dimension": len(embedding),
            "embedding": embedding  # Already a list from get_vector()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vector {vector_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
