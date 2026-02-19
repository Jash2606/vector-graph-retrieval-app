# File: app/controllers/edge_controller.py
"""Controller for edge/relationship operations"""
from typing import Dict, Any
import logging

from app.models import EdgeInput
from app.repositories.neo4j_repository import Neo4jRepository
from app.core.exceptions import EdgeCreationError, InvalidEdgeTypeError
from app.core.constants import ALLOWED_EDGE_TYPES

logger = logging.getLogger(__name__)


class EdgeController:
    """Handles business logic for edge operations"""

    def __init__(self, neo4j_repo: Neo4jRepository):
        self.neo4j_repo = neo4j_repo

    def create_edge(self, edge_input: EdgeInput) -> Any:
        """Create a relationship between nodes"""
        # Validate edge type
        if edge_input.type not in ALLOWED_EDGE_TYPES:
            raise InvalidEdgeTypeError(
                edge_input.type, list(ALLOWED_EDGE_TYPES))

        try:
            result = self.neo4j_repo.create_edge(
                source_id=edge_input.source,
                target_id=edge_input.target,
                edge_type=edge_input.type,
                weight=edge_input.weight,
                metadata=edge_input.metadata
            )

            if not result:
                raise EdgeCreationError(
                    edge_input.source,
                    edge_input.target,
                    "One or both nodes do not exist"
                )

            return result
        except InvalidEdgeTypeError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating edge: {str(e)}")
            raise EdgeCreationError(
                edge_input.source, edge_input.target, str(e))

    def get_edge(self, edge_id: str) -> Dict[str, Any]:
        """Retrieve an edge by ID"""
        edge = self.neo4j_repo.get_edge(edge_id)
        if not edge:
            raise EdgeCreationError(
                "unknown", "unknown", f"Edge {edge_id} not found")
        return edge
