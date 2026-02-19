# File: app/controllers/search_controller.py
"""Controller for search operations"""
from typing import List, Dict
import logging
import spacy
import math
import numpy as np

from app.models import SearchResult, HybridSearchResponse, HybridSearchResultItem
from app.repositories.neo4j_repository import Neo4jRepository
from app.repositories.vector_repository import VectorRepository
from app.services.embedding import embedding_service
from app.core.exceptions import SearchError

logger = logging.getLogger(__name__)

# Load Spacy model for query parsing
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("Spacy model not found. Query parsing will be limited.")
    nlp = None


class SearchController:
    """Handles business logic for search operations"""

    def __init__(self, neo4j_repo: Neo4jRepository,
                 vector_repo: VectorRepository):
        self.neo4j_repo = neo4j_repo
        self.vector_repo = vector_repo

    def vector_search(self, query_text: str, top_k: int) -> List[SearchResult]:
        """Perform pure vector search"""
        try:
            # Encode query
            query_vector = embedding_service.encode(query_text)

            # Search FAISS
            distances, indices = self.vector_repo.search(query_vector, top_k)

            results = []
            for i, idx in enumerate(indices):
                if idx == -1:
                    continue

                doc_id = self.vector_repo.get_document_id(idx)
                if not doc_id:
                    continue

                # Fetch details from Neo4j
                node = self.neo4j_repo.get(doc_id)
                if node:
                    results.append(SearchResult(
                        id=doc_id,
                        text=node.get('text'),
                        score=float(distances[i]),
                        metadata=node,
                        graph_info={}
                    ))

            return results
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}", exc_info=True)
            raise SearchError(f"Vector search failed: {str(e)}")

    def graph_search(
            self,
            start_id: str,
            depth: int,
            relationship_types: List[str] = None) -> Dict:
        """Perform pure graph traversal"""
        try:
            return self.neo4j_repo.graph_search(
                start_id, depth, relationship_types)
        except Exception as e:
            logger.error(f"Graph search failed: {str(e)}", exc_info=True)
            raise SearchError(f"Graph search failed: {str(e)}")

    def hybrid_search(
            self,
            query_text: str,
            vector_weight: float,
            graph_weight: float,
            top_k: int,
            graph_depth: int,
            query_embedding: List[float] = None) -> HybridSearchResponse:
        """Perform hybrid vector + graph search"""
        try:
            # Normalize weights
            total = vector_weight + graph_weight
            if total <= 0:
                alpha, beta = 1.0, 0.0
            else:
                alpha = vector_weight / total
                beta = graph_weight / total

            # Extract entities from query
            query_entities = []
            if nlp:
                doc = nlp(query_text)
                query_entities = [ent.text for ent in doc.ents]
            logger.info(f"Query Entities: {query_entities}")

            # Vector search for candidates
            if query_embedding:
                query_vector = np.array(query_embedding, dtype=np.float32)
                distances, indices = self.vector_repo.search(
                    query_vector, top_k * 3)

                vector_results = []
                for i, idx in enumerate(indices):
                    if idx == -1:
                        continue
                    doc_id = self.vector_repo.get_document_id(idx)
                    if not doc_id:
                        continue

                    node = self.neo4j_repo.get(doc_id)
                    if node:
                        vector_results.append(SearchResult(
                            id=doc_id,
                            text=node.get('text'),
                            score=float(distances[i]),
                            metadata=node,
                            graph_info={}
                        ))
            else:
                vector_results = self.vector_search(query_text, top_k * 3)

            candidates: Dict[str, SearchResult] = {
                r.id: r for r in vector_results}

            # Graph expansion from query entities
            if query_entities:
                entity_docs = self.neo4j_repo.find_entity_documents(
                    query_entities, limit=50)
                for node, edge_weight in entity_docs:
                    doc_id = node.get("id")
                    if doc_id not in candidates:
                        candidates[doc_id] = SearchResult(
                            id=doc_id, text=node.get("text"), score=0.0, metadata=dict(node), graph_info={
                                "hops": 1, "expansion_weight": edge_weight})
                    else:
                        gi = candidates[doc_id].graph_info
                        gi["hops"] = 1
                        gi["expansion_weight"] = edge_weight

            if not candidates:
                return HybridSearchResponse(
                    query_text=query_text,
                    vector_weight=vector_weight,
                    graph_weight=graph_weight,
                    results=[]
                )

            candidate_ids = list(candidates.keys())

            # Get connectivity scores
            connectivity_scores = self.neo4j_repo.get_connectivity_scores(
                candidate_ids)

            # Calculate scale
            if connectivity_scores:
                avg_c = sum(connectivity_scores.values()) / \
                    len(connectivity_scores)
            else:
                avg_c = 1.0
            graph_scale = max(1.0, avg_c)

            # Calculate final scores
            final_results_items = []
            for doc_id, r in candidates.items():
                # Vector component
                raw_v = r.score
                v_score_norm = max(0.0, min(1.0, raw_v))

                # Graph connectivity component
                c_raw = connectivity_scores.get(doc_id, 0.0)
                c_score_norm = 1.0 - math.exp(-c_raw / graph_scale)

                hops = r.graph_info.get("hops", 0)

                if beta > 0:
                    g_component = c_score_norm / (1 + hops)
                else:
                    g_component = 0.0

                # Final hybrid score
                final_score = (alpha * v_score_norm) + (beta * g_component)

                # Construct info dict
                info = {
                    "hop": hops,
                    "raw_vector_score": raw_v,
                    "connectivity_score_raw": c_raw
                }
                if "expansion_weight" in r.graph_info:
                    info["edge_weight"] = r.graph_info["expansion_weight"]

                final_results_items.append(HybridSearchResultItem(
                    id=doc_id,
                    text=r.text,
                    vector_score=raw_v,
                    graph_score=g_component,
                    final_score=final_score,
                    info=info
                ))

            # Sort and return top-k
            final_results_items.sort(key=lambda x: x.final_score, reverse=True)

            return HybridSearchResponse(
                query_text=query_text,
                vector_weight=vector_weight,
                graph_weight=graph_weight,
                results=final_results_items[:top_k]
            )
        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}", exc_info=True)
            raise SearchError(f"Hybrid search failed: {str(e)}")
