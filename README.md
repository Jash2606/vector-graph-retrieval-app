# 🧠 Hybrid Vector-Graph Retrieval System

A production-ready **semantic search engine** that combines **vector similarity** (FAISS) with **graph-based knowledge traversal** (Neo4j) to deliver contextually rich and highly relevant search results.

---

## 🎯 Overview

This system implements a **hybrid retrieval approach** that overcomes the limitations of pure vector search by incorporating graph-based contextual relationships. It's designed for applications requiring:

- **Semantic understanding** of queries
- **Contextual relevance** beyond keyword matching
- **Knowledge graph traversal** for discovering connected information
- **Entity extraction** and relationship mapping

**Use Cases**:
- Knowledge base search
- Document discovery systems
- Research paper retrieval
- Content recommendation engines
- FAQ systems with context awareness

---

## ✨ Key Features

### Search Capabilities
- 🔍 **Vector Search**: Pure semantic similarity using sentence transformers
- 🕸️ **Graph Search**: Structural traversal from start nodes with depth control
- 🎯 **Hybrid Search**: Combines vector scores + graph connectivity for optimal results
- 📊 **Configurable Weighting**: Adjust vector vs. graph influence dynamically

### Data Management
- 📄 **Document Ingestion**: Automatic chunking, embedding, and entity extraction
- 🔗 **Relationship Mapping**: Auto-creates entity-document relationships
- 🗃️ **Dual Storage**: FAISS for vectors, Neo4j for graph structure
- 🔧 **CRUD Operations**: Full document and edge management

### Developer Experience
- 🛡️ **MVC Architecture**: Clean separation of concerns
- 🚨 **Custom Error Handling**: Meaningful error messages with proper HTTP codes
- 🔒 **Security**: Input validation, Cypher injection prevention
- 📊 **Debug Tools**: Database inspector for development
- 🎨 **Interactive UI**: Streamlit frontend with graph visualization

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit Frontend                      │
│  (Search Interface + Graph Visualization + DB Inspector)     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────────┐
│                      FastAPI Backend                         │
│  ┌────────────┬───────────────┬──────────────┬────────────┐ │
│  │   Routes   │  Controllers  │ Repositories │  Services  │ │
│  │  (API Layer)│ (Business     │ (Data Access)│ (Utilities)│ │
│  │            │   Logic)      │              │            │ │
│  └────────────┴───────────────┴──────────────┴────────────┘ │
└──────────────────────┬────────────────────┬─────────────────┘
                       │                    │
         ┌─────────────▼──────┐  ┌─────────▼──────────┐
         │    Neo4j Graph DB   │  │   FAISS Vector     │
         │  (Relationships +   │  │   Index (Semantic  │
         │   Entities)         │  │   Embeddings)      │
         └─────────────────────┘  └────────────────────┘
```

**For detailed architecture, see [ARCHITECTURE.md](./ARCHITECTURE_OVERVIEW.md)**

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Neo4j 5.12** - Graph database for relationships
- **FAISS** - Facebook AI Similarity Search for vectors
- **Sentence Transformers** - Semantic embeddings (`all-MiniLM-L6-v2`)
- **spaCy** - NLP for entity extraction (`en_core_web_sm`)

### Frontend
- **Streamlit** - Interactive web UI
- **streamlit-agraph** - Graph visualization

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Pydantic** - Data validation
- **Python 3.10+** - Core language

---

## 📁 Project Structure

```
vector-graph-retrieval-app/
├── app/
│   ├── api/                      # API layer (MVC)
│   │   ├── routes/              # HTTP endpoints
│   │   │   ├── health.py        # Health checks
│   │   │   ├── documents.py     # Document CRUD
│   │   │   ├── edges.py         # Relationship management
│   │   │   ├── search.py        # All search types
│   │   │   └── debug.py         # Debug/inspector tools
│   │   └── dependencies.py      # Dependency injection
│   │
│   ├── controllers/             # Business logic layer
│   │   ├── document_controller.py
│   │   ├── edge_controller.py
│   │   └── search_controller.py
│   │
│   ├── repositories/            # Data access layer
│   │   ├── neo4j_repository.py  # Graph DB operations
│   │   └── vector_repository.py # FAISS operations
│   │
│   ├── services/                # Utility services
│   │   ├── ingestion.py         # Document processing
│   │   └── search.py            # Search algorithms (legacy)
│   │
│   ├── models/                  # Data models
│   │   └── schemas.py           # Pydantic schemas
│   │
│   ├── core/                    # Core utilities
│   │   ├── exceptions.py        # Custom exceptions
│   │   └── constants.py         # App constants
│   │
│   ├── config.py                # Configuration management
│   ├── database.py              # DB connections
│   └── main.py                  # FastAPI app entry
│
├── frontend/
│   └── streamlit_app.py         # Streamlit UI
│
├── data/                        # Persistent data
│   ├── faiss_index.bin          # FAISS index file
│   ├── faiss_map.pkl            # Vector-to-doc mapping
│   └── neo4j/                   # Neo4j data volumes
│
├── docker-compose.yml           # Neo4j container config
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

---

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.10+**
- **Docker & Docker Compose**
- **Git**

### Step 1: Clone Repository
```bash
git clone https://github.com/Jash2606/vector-graph-retrieval-app.git
cd vector-graph-retrieval-app
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Step 4: Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

**Key Environment Variables**:
```env
API_URL=http://localhost:8000/v1
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
VECTOR_DIM=384
```

### Step 5: Start Neo4j Database
```bash
docker-compose up -d

# Wait 15-20 seconds for Neo4j to initialize
# Verify at http://localhost:7474 (Browser UI)
```

### Step 6: Start Backend Server
```bash
uvicorn app.main:app --reload

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Step 7: Start Frontend (Optional)
```bash
# In a new terminal
streamlit run frontend/streamlit_app.py

# UI opens at http://localhost:8501
```

---

## 💡 Usage

### 1. Ingest Documents

**Via API** (Recommended for programmatic use):
```bash
curl -X POST "http://localhost:8000/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Albert Einstein was a German-born theoretical physicist...",
    "title": "Albert Einstein Biography"
  }'
```

**Via Frontend**:
1. Go to "Ingestion" tab
2. Enter title and text
3. Click "Ingest Document"

### 2. Search Documents

#### Vector Search (Pure Semantic)
```bash
curl -X POST "http://localhost:8000/search/vector" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Who discovered relativity?",
    "top_k": 5
  }'
```

#### Graph Search (Structural Traversal)
```bash
curl -X GET "http://localhost:8000/search/graph?start_id=<DOC_ID>&depth=2"
```

#### Hybrid Search (Best Results)
```bash
curl -X POST "http://localhost:8000/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Einstein relativity theory",
    "vector_weight": 0.7,
    "graph_weight": 0.3,
    "top_k": 5
  }'
```

### 3. Database Inspector (Frontend Only)
Go to "Database Inspector" tab to explore:
- **Neo4j Documents**: All stored documents
- **Neo4j Entities**: Extracted entities
- **FAISS Index**: Vector embeddings metadata

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000/v1
```

### Endpoints

#### Health Check
```http
GET /health
```
**Response**: `{"status": "healthy", "neo4j": "connected", "faiss": "ready"}`

---

#### Create Document
```http
POST /documents
Content-Type: application/json

{
  "text": "Document content here...",
  "title": "Optional title"
}
```
**Returns**: Document ID and metadata

---

#### Get Document
```http
GET /documents/{doc_id}
```
**Returns**: Full document with text, embeddings, relationships

---

#### Update Document
```http
PUT /documents/{doc_id}
Content-Type: application/json

{
  "text": "Updated content",
  "title": "New title"
}
```

---

#### Delete Document
```http
DELETE /documents/{doc_id}
```
**Returns**: Success confirmation

---

#### Create Relationship
```http
POST /edges
Content-Type: application/json

{
  "source_id": "doc-123",
  "target_id": "doc-456",
  "edge_type": "RELATED_TO",
  "weight": 0.85
}
```
**Allowed Edge Types**: `RELATED_TO`, `MENTIONS`, `CITES`, `REQUIRES`

---

#### Vector Search
```http
POST /search/vector
Content-Type: application/json

{
  "query_text": "Your search query",
  "top_k": 5
}
```
**Returns**: Top K semantically similar documents

---

#### Graph Search
```http
GET /search/graph?start_id={doc_id}&depth={1-3}
```
**Returns**: Graph structure (nodes + edges) within depth

---

#### Hybrid Search
```http
POST /search/hybrid
Content-Type: application/json

{
  "query_text": "Your query",
  "vector_weight": 0.7,
  "graph_weight": 0.3,
  "top_k": 10,
  "graph_expand_depth": 1
}
```
**Returns**: Ranked results combining vector + graph scores

---

## 🔍 Search Algorithms

### 1. Vector Search
- Uses **cosine similarity** on normalized embeddings
- Model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- Fast retrieval via FAISS `IndexFlatIP`

### 2. Graph Search
- BFS/DFS traversal from start node
- Configurable depth (1-3 recommended)
- Returns full subgraph structure

### 3. Hybrid Search (Advanced)
**Scoring Formula**:
```
final_score = α × vector_score + β × graph_score

where:
  vector_score = normalized cosine similarity
  graph_score = f(connectivity, hops, entity_matches)
  α + β = 1.0
```

**Graph Score Components**:
- **Connectivity**: Number of relationships
- **Hops**: Distance from query entities
- **Expansion Bonus**: Bonus for multi-hop discovery

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed scoring breakdown.

---

## 🧪 Testing

### Manual Testing
1. **Ingest sample data**: Use the frontend or API to add documents
2. **Try all search types**: Vector, Graph, Hybrid
3. **Inspect database**: Use Database Inspector tab

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Create test document
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{"text": "Test document", "title": "Test"}'

# Search
curl -X POST http://localhost:8000/search/vector \
  -H "Content-Type: application/json" \
  -d '{"query_text": "test", "top_k": 5}'
```
---

## 📈 Performance Considerations

### Scalability
- **FAISS**: Handles millions of vectors efficiently
- **Neo4j**: Optimized for graph traversal queries
- **Caching**: Add Redis for frequent query caching (future enhancement)

### Optimization Tips
1. **Limit graph depth**: Keep `depth ≤ 2` for graph search
2. **Batch ingestion**: Use bulk import for large datasets
3. **Index tuning**: For >100K documents, consider `IndexIVFFlat`

---

## 🔮 Future Enhancements

- [ ] **Reranking**: Cross-encoder for final result refinement
- [ ] **Query expansion**: Synonym and paraphrase generation
- [ ] **Multi-modal**: Image + text embeddings
- [ ] **User feedback**: Relevance feedback loop
- [ ] **Caching**: Redis for hot queries
- [ ] **Monitoring**: Prometheus + Grafana metrics
- [ ] **Batch API**: Bulk operations endpoint

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Support

For issues, questions, or feature requests, please open a GitHub issue.

---

**Built with ❤️ using FastAPI, Neo4j, and FAISS**
