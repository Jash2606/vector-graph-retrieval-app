# File: app/controllers/document_controller.py
"""Controller for document operations"""
from typing import Dict, Any
import uuid
import logging

from app.models import DocumentInput, Document, NodeUpdate
from app.repositories.neo4j_repository import Neo4jRepository
from app.repositories.vector_repository import VectorRepository
from app.services.embedding import embedding_service
from app.services.ingestion import clean_text, recursive_chunking, _create_semantic_edges, _extract_and_link_entities
from app.core.exceptions import NodeNotFoundError, IngestionError
from langdetect import detect

logger = logging.getLogger(__name__)


class DocumentController:
    """Handles business logic for document operations"""

    def __init__(self, neo4j_repo: Neo4jRepository,
                 vector_repo: VectorRepository):
        self.neo4j_repo = neo4j_repo
        self.vector_repo = vector_repo

    def create_document(self, doc_input: DocumentInput) -> Document:
        """Process and ingest a document"""
        try:
            logger.info(
                f"--- Starting Ingestion for Document: {doc_input.title} ---")

            # 1. Clean Text
            cleaned_text = clean_text(doc_input.text)

            # 2. Language Detection
            try:
                lang = detect(cleaned_text)
                logger.info(f"Detected Language: {lang}")
            except Exception as e:
                logger.warning(f"Language detection failed: {str(e)}")
                lang = "unknown"

            # 3. Chunking
            chunks = recursive_chunking(cleaned_text)
            logger.info(f"Generated {len(chunks)} chunks.")

            first_doc_id = None

            for i, chunk_text in enumerate(chunks):
                doc_id = str(uuid.uuid4())
                if i == 0:
                    first_doc_id = doc_id

                chunk_title = f"{
                    doc_input.title} (Chunk {
                    i +
                    1})" if doc_input.title else f"Chunk {
                    i +
                    1}"

                # 4. Generate Embedding
                embedding = embedding_service.encode(chunk_text)

                # 5. Add to FAISS
                vector_id = self.vector_repo.add_vector(embedding, doc_id)

                # 6 Create Node in Neo4j
                self.neo4j_repo.create_document_node(
                    doc_id=doc_id,
                    text=chunk_text,
                    title=chunk_title,
                    vector_id=vector_id,
                    lang=lang,
                    chunk_index=i,
                    metadata=doc_input.metadata
                )

                # 7. Semantic Edge Creation
                _create_semantic_edges(doc_id, embedding, vector_id)

                # 8. NER Extraction & Edge Creation
                _extract_and_link_entities(doc_id, chunk_text)

            return Document(
                id=first_doc_id if first_doc_id else "error",
                text=cleaned_text,
                metadata=doc_input.metadata,
                vector_id=vector_id
            )
        except Exception as e:
            logger.error(f"Document ingestion failed: {str(e)}", exc_info=True)
            raise IngestionError(str(e))

    def get_document(self, node_id: str) -> Dict[str, Any]:
        """Retrieve a document by ID"""
        node = self.neo4j_repo.get(node_id)
        if not node:
            raise NodeNotFoundError(node_id)
        return node

    def update_document(self, node_id: str,
                        update_data: NodeUpdate) -> Dict[str, Any]:
        """Update document properties"""
        # Build update dict
        update_dict = {}
        if update_data.text is not None:
            update_dict['text'] = update_data.text
        if update_data.title is not None:
            update_dict['title'] = update_data.title
        if update_data.metadata:
            update_dict.update(update_data.metadata)

        # Update in Neo4j
        if update_dict:
            node = self.neo4j_repo.update(node_id, update_dict)
            if not node:
                raise NodeNotFoundError(node_id)
        else:
            node = self.neo4j_repo.get(node_id)

        # Regenerate embedding if requested
        if update_data.regen_embedding and node:
            text_to_embed = update_data.text if update_data.text else node.get(
                'text')
            if text_to_embed and node.get('vector_id') is not None:
                # Regenerate embedding
                embedding = embedding_service.encode(text_to_embed)
                self.vector_repo.update_document(node_id, embedding)
                logger.info(f"Regenerated embedding for node {node_id}")

                # Delete old relationships
                self.neo4j_repo.delete_relationships(
                    node_id, ['RELATED_TO', 'MENTIONS'])
                logger.info(f"Deleted old relationships for node {node_id}")

                # Re-create relationships
                _create_semantic_edges(node_id, embedding, -1)
                _extract_and_link_entities(node_id, text_to_embed)

                # Refresh node data
                node = self.neo4j_repo.get(node_id)

        return node

    def delete_document(self, node_id: str) -> bool:
        """Delete a document"""
        # Delete from Neo4j
        deleted = self.neo4j_repo.delete(node_id)

        # Remove from FAISS
        self.vector_repo.remove_document(node_id)

        if not deleted:
            raise NodeNotFoundError(node_id)

        return True
