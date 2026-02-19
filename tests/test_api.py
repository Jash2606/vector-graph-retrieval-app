"""
API Tests for Hybrid Vector-Graph Retrieval API

"""
import sys
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch

# Mock heavy dependencies before importing app
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['spacy'] = MagicMock()
sys.modules['langdetect'] = MagicMock()
sys.modules['neo4j'] = MagicMock()
sys.modules['faiss'] = MagicMock()

mock_embedding_model = MagicMock()
mock_embedding_model.encode = MagicMock(return_value=np.random.rand(384).astype(np.float32))
sys.modules['sentence_transformers'].SentenceTransformer = MagicMock(return_value=mock_embedding_model)
sys.modules['langdetect'].detect = MagicMock(return_value="en")

mock_nlp = MagicMock()
mock_doc = MagicMock()
mock_doc.ents = []
mock_nlp.return_value = mock_doc
sys.modules['spacy'].load = MagicMock(return_value=mock_nlp)

from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_neo4j_repository, get_vector_repository


# ============== Fixtures ==============

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_repos():
    """Mock both repositories"""
    neo4j_repo = Mock()
    vector_repo = Mock()
    
    # Default Neo4j responses
    neo4j_repo.get.return_value = {
        "id": "doc-123",
        "text": "Sample document text",
        "title": "Test Document",
        "vector_id": 0,
        "relationships": []
    }
    neo4j_repo.create_document_node.return_value = {"id": "doc-123", "text": "Text", "vector_id": 0}
    neo4j_repo.update.return_value = {"id": "doc-123", "text": "Updated", "title": "Updated"}
    neo4j_repo.delete.return_value = True
    neo4j_repo.create_edge.return_value = {"type": "RELATED_TO", "weight": 1.0}
    neo4j_repo.get_edge.return_value = {"id": "edge-123", "type": "RELATED_TO", "source": "a", "target": "b"}
    neo4j_repo.graph_search.return_value = {"nodes": [{"id": "n1"}], "edges": []}
    neo4j_repo.get_connectivity_scores.return_value = {"doc-0": 5.0}
    neo4j_repo.find_entity_documents.return_value = []
    
    # Default Vector responses
    vector_repo.add_vector.return_value = 0
    vector_repo.search.return_value = (np.array([0.95, 0.85]), np.array([0, 1]))
    vector_repo.get_document_id.side_effect = lambda i: f"doc-{i}" if i >= 0 else None
    vector_repo.remove_document.return_value = None
    
    # Override dependencies
    app.dependency_overrides[get_neo4j_repository] = lambda: neo4j_repo
    app.dependency_overrides[get_vector_repository] = lambda: vector_repo
    
    yield {"neo4j": neo4j_repo, "vector": vector_repo}
    
    app.dependency_overrides.clear()


# ============== Health APIs ==============

def test_root_api(client):
    """GET / - Root endpoint"""
    response = client.get("/v1/")
    assert response.status_code == 200
    assert "message" in response.json()


@patch('app.api.routes.health.neo4j_driver')
def test_health_api(mock_driver, client):
    """GET /health - Health check"""
    mock_driver.ping.return_value = None  # ping() returns None on success

    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch('app.api.routes.health.neo4j_driver')
def test_health_api_db_down(mock_driver, client):
    """GET /health - Returns 503 when DB is unreachable"""
    mock_driver.ping.side_effect = Exception("Connection refused")

    response = client.get("/v1/health")
    assert response.status_code == 503


# ============== Document APIs ==============

def test_create_document_api(client, mock_repos):
    """POST /nodes - Create document"""
    with patch('app.controllers.document_controller.clean_text', return_value="Cleaned"), \
         patch('app.controllers.document_controller.recursive_chunking', return_value=["Chunk"]), \
         patch('app.controllers.document_controller.embedding_service') as mock_embed, \
         patch('app.controllers.document_controller._create_semantic_edges'), \
         patch('app.controllers.document_controller._extract_and_link_entities'), \
         patch('app.controllers.document_controller.detect', return_value="en"):
        
        mock_embed.encode.return_value = np.array([0.1] * 384)
        
        response = client.post("/v1/nodes", json={
            "text": "Test document content",
            "title": "Test Title",
            "metadata": {"key": "value"}
        })
        
        assert response.status_code == 200
        assert "id" in response.json()


def test_get_document_api(client, mock_repos):
    """GET /nodes/{id} - Get document"""
    response = client.get("/v1/nodes/doc-123")
    
    assert response.status_code == 200
    assert response.json()["id"] == "doc-123"


def test_get_document_not_found_api(client, mock_repos):
    """GET /nodes/{id} - Document not found returns 404"""
    mock_repos["neo4j"].get.return_value = None
    
    response = client.get("/v1/nodes/nonexistent")
    
    assert response.status_code == 404


def test_update_document_api(client, mock_repos):
    """PUT /nodes/{id} - Update document"""
    response = client.put("/v1/nodes/doc-123", json={
        "text": "Updated text",
        "title": "New Title",
        "regen_embedding": False
    })
    
    assert response.status_code == 200


def test_delete_document_api(client, mock_repos):
    """DELETE /nodes/{id} - Delete document"""
    response = client.delete("/v1/nodes/doc-123")
    
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"


def test_delete_document_not_found_api(client, mock_repos):
    """DELETE /nodes/{id} - Delete non-existent returns 404"""
    mock_repos["neo4j"].delete.return_value = False
    
    response = client.delete("/v1/nodes/nonexistent")
    
    assert response.status_code == 404


# ============== Edge APIs ==============

def test_create_edge_api(client, mock_repos):
    """POST /edges - Create edge"""
    response = client.post("/v1/edges", json={
        "source": "node-1",
        "target": "node-2",
        "type": "RELATED_TO",
        "weight": 1.0
    })
    
    assert response.status_code == 200


def test_create_edge_invalid_type_api(client, mock_repos):
    """POST /edges - Invalid edge type returns 400"""
    response = client.post("/v1/edges", json={
        "source": "node-1",
        "target": "node-2",
        "type": "INVALID_TYPE",
        "weight": 1.0
    })
    
    assert response.status_code == 400


def test_get_edge_api(client, mock_repos):
    """GET /edges/{id} - Get edge"""
    response = client.get("/v1/edges/edge-123")
    
    assert response.status_code == 200


# ============== Search APIs ==============

def test_vector_search_api(client, mock_repos):
    """POST /search/vector - Vector search"""
    with patch('app.controllers.search_controller.embedding_service') as mock_embed:
        mock_embed.encode.return_value = np.array([0.1] * 384, dtype=np.float32)
        
        response = client.post("/v1/search/vector", json={
            "query_text": "test query",
            "top_k": 5
        })
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_graph_search_api(client, mock_repos):
    """GET /search/graph - Graph traversal"""
    response = client.get("/v1/search/graph", params={
        "start_id": "node-1",
        "depth": 2
    })
    
    assert response.status_code == 200
    assert "nodes" in response.json()


def test_hybrid_search_api(client, mock_repos):
    """POST /search/hybrid - Hybrid search"""
    with patch('app.controllers.search_controller.embedding_service') as mock_embed:
        mock_embed.encode.return_value = np.array([0.1] * 384, dtype=np.float32)
        
        response = client.post("/v1/search/hybrid", json={
            "query_text": "hybrid search test",
            "top_k": 5,
            "vector_weight": 0.7,
            "graph_weight": 0.3,
            "graph_expand_depth": 2
        })
        
        assert response.status_code == 200
        assert "results" in response.json()


# ============== Validation ==============

def test_invalid_json_api(client):
    """Invalid JSON returns 422"""
    response = client.post(
        "/v1/nodes",
        content="invalid json{",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422


def test_missing_required_field_api(client):
    """Missing required field returns 422"""
    response = client.post("/v1/nodes", json={})  # Missing 'text'
    
    assert response.status_code == 422
