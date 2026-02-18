# 🏛️ System Architecture 




## 🎯 What Does This System Do?

This is a **smart search engine** that finds documents using two complementary approaches:

1. **Vector Search**: Understands the *meaning* of your query (semantic search)
2. **Graph Search**: Explores *connections* between documents and entities

By combining both, you get search results that are both semantically relevant AND contextually connected.

---

## 🏠 The Big Picture

The system implements a **three-tier architecture** with clear separation of concerns:

```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[Streamlit Frontend]
    end
    
    subgraph "Application Layer"
        API[FastAPI Routes]
        CTRL[Controllers]
        SVC[Services]
    end
    
    subgraph "Data Layer"
        REPO[Repositories]
        NEO[(Neo4j Graph DB)]
        FAISS[(FAISS Vector Index)]
    end
    
    UI -->|HTTP REST| API
    API --> CTRL
    CTRL --> SVC
    CTRL --> REPO
    REPO --> NEO
    REPO --> FAISS
    
    style UI fill:#e1f5ff
    style NEO fill:#ffe1e1
    style FAISS fill:#e1ffe1
```

**What Each Layer Does:**

| Layer | Components | Purpose |
|-------|-----------|----------|
| **Presentation** | Streamlit UI | What you see and interact with |
| **Application** | FastAPI, Controllers, Services | Processes your requests |
| **Data** | Repositories, Neo4j, FAISS | Stores and retrieves data |

---

## 🧱 Backend Architecture: The MVC Pattern

The backend follows the **MVC (Model-View-Controller)** pattern, but adapted for APIs. Think of it as a **layered cake** - each layer has a specific job:

```mermaid
graph LR
    subgraph "API Layer (Routes)"
        R1[health.py]
        R2[documents.py]
        R3[edges.py]
        R4[search.py]
        R5[debug.py]
    end
    
    subgraph "Controller Layer"
        C1[DocumentController]
        C2[EdgeController]
        C3[SearchController]
    end
    
    subgraph "Repository Layer"
        RP1[Neo4jRepository]
        RP2[VectorRepository]
    end
    
    R2 --> C1
    R3 --> C2
    R4 --> C3
    R5 --> RP1
    R5 --> RP2
    
    C1 --> RP1
    C1 --> RP2
    C2 --> RP1
    C3 --> RP1
    C3 --> RP2
    
    style R1 fill:#b3d9ff
    style R2 fill:#b3d9ff
    style R3 fill:#b3d9ff
    style R4 fill:#b3d9ff
    style R5 fill:#b3d9ff
```

**How Data Flows:**
1. **Routes** receive HTTP requests and validate input
2. **Controllers** contain business logic and coordinate operations
3. **Repositories** talk to databases (Neo4j & FAISS)

### Why This Structure?

| Layer | Responsibility | Why Separate? |
|-------|---------------|---------------|
| **Routes** | HTTP handling | Easy to change API endpoints |
| **Controllers** | Business logic | Logic stays in one place |
| **Repositories** | Data access | Can swap databases easily |
| **Services** | Utilities | Reusable across controllers |

---

## 📁 Folder Structure Explained

```
app/
├── main.py              ← Application entry point
├── config.py            ← Configuration settings
├── database.py          ← Database connections
│
├── api/                 ← API LAYER
│   ├── routes/          ← HTTP endpoints
│   │   ├── health.py    ← Health check endpoint
│   │   ├── documents.py ← Document CRUD
│   │   ├── edges.py     ← Relationship management
│   │   ├── search.py    ← Search endpoints
│   │   └── debug.py     ← Debug tools
│   └── dependencies.py  ← Dependency injection setup
│
├── controllers/         ← BUSINESS LOGIC LAYER
│   ├── document_controller.py  ← Document operations
│   ├── edge_controller.py      ← Relationship operations
│   └── search_controller.py    ← Search operations
│
├── repositories/        ← DATA ACCESS LAYER
│   ├── base.py          ← Base repository interface
│   ├── neo4j_repository.py  ← Neo4j operations
│   └── vector_repository.py ← FAISS operations
│
├── services/            ← UTILITY SERVICES
│   ├── embedding.py     ← Text → Vector conversion
│   └── ingestion.py     ← Document processing
│
├── models/              ← DATA MODELS
│   └── schemas.py       ← Pydantic request/response models
│
└── core/                ← CORE UTILITIES
    ├── constants.py     ← App-wide constants
    └── exceptions.py    ← Custom error types
```

---

## 📥 How Document Ingestion Works

When you add a new document, here's what happens step by step:

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Controller
    participant Service
    participant Neo4j
    participant FAISS
    
    User->>Frontend: Enter document text + title
    Frontend->>API: POST /documents {text, title}
    API->>Controller: create_document(text, title)
    
    Controller->>Service: ingest_document(text, title)
    Service->>Service: 1. Clean text
    Service->>Service: 2. Chunk text (256 tokens)
    Service->>Service: 3. Generate embedding
    Service->>Service: 4. Extract entities (spaCy)
    Service-->>Controller: doc_data
    
    Controller->>Neo4j: create_document_node(doc_data)
    Neo4j-->>Controller: node
    
    Controller->>FAISS: add_vector(embedding, doc_id)
    FAISS-->>Controller: vector_id
    
    Controller->>Neo4j: create_entity_relationships()
    
    Controller-->>API: document_response
    API-->>Frontend: 201 Created
    Frontend-->>User: Show success + document ID
```

### The 5 Processing Steps:

| Step | What Happens | Why? |
|------|-------------|------|
| **1. Clean** | Remove HTML, fix whitespace | Normalize text |
| **2. Chunk** | Split into 256-token pieces | Handle long documents |
| **3. Embed** | Convert to 384-dim vector | Enable semantic search |
| **4. Store** | Save to Neo4j + FAISS | Dual storage |
| **5. Connect** | Create edges + extract entities | Build knowledge graph |

### What Gets Created?

After ingestion, you have:

1. **Document Node** in Neo4j (stores text, title, metadata)
2. **Vector** in FAISS (384-dimensional embedding)
3. **Entity Nodes** in Neo4j (people, organizations, places, dates)
4. **MENTIONS Edges** connecting document to its entities
5. **RELATED_TO Edges** connecting to similar documents

---

## 🔍 How Search Works

### Vector Search (Semantic)

Finds documents by **meaning**, not just keywords:

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Controller
    participant FAISS
    participant Neo4j
    
    User->>Frontend: Enter query: "Einstein relativity"
    Frontend->>API: POST /search/vector {query, top_k=5}
    API->>Controller: vector_search(query, 5)
    
    Controller->>Controller: Encode query to vector
    Controller->>FAISS: search(query_vector, k=5)
    FAISS-->>Controller: [distances, indices]
    
    loop For each vector_id in indices
        Controller->>FAISS: get_document_id(vector_id)
        Controller->>Neo4j: get_document_by_id(doc_id)
        Controller->>Controller: Build SearchResult
    end
    
    Controller-->>API: [results]
    API-->>Frontend: JSON response
    Frontend-->>User: Display ranked results
```

### Graph Search (Structural)

Explores **connections** between documents and entities:

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Controller
    participant Neo4j
    
    User->>Frontend: Select start document + depth
    Frontend->>API: GET /search/graph?start_id=X&depth=2
    API->>Controller: graph_search(start_id, depth=2)
    
    Controller->>Neo4j: Cypher query (BFS traversal)
    Note over Neo4j: MATCH (start)-[*0..2]-(n)<br/>RETURN nodes + edges
    Neo4j-->>Controller: Graph data
    
    Controller->>Controller: Build scored_edges
    Controller->>Controller: Sort by edge weight
    
    Controller-->>API: {nodes, edges, scored_edges}
    API-->>Frontend: JSON response
    Frontend-->>User: Render graph visualization
```

### Hybrid Search (Best of Both)

Combines vector similarity + graph connections:

```mermaid
sequenceDiagram
    participant User
    participant Controller
    participant FAISS
    participant Neo4j
    participant Scorer
    
    User->>Controller: hybrid_search("Einstein", α=0.7, β=0.3)
    
    Note over Controller: Phase 1: Entity Extraction
    Controller->>Controller: Extract entities ["Einstein"]
    
    Note over Controller: Phase 2: Vector Search
    Controller->>FAISS: Top-K vector search
    FAISS-->>Controller: Candidate Set A
    
    Note over Controller: Phase 3: Graph Expansion
    Controller->>Neo4j: Find docs mentioning "Einstein"
    Neo4j-->>Controller: Candidate Set B
    
    Note over Controller: Phase 4: Merge & Deduplicate
    Controller->>Controller: Candidates = A ∪ B
    
    Note over Controller: Phase 5: Score Calculation
    loop For each candidate
        Controller->>FAISS: Get vector score
        Controller->>Neo4j: Get connectivity score
        Controller->>Scorer: Compute final score
    end
    
    Note over Controller: Phase 6: Ranking
    Controller->>Controller: Sort by final_score
    Controller-->>User: Top-K hybrid results
```

**Hybrid Scoring Formula:**
```
final_score = α × vector_score + β × graph_score

where α + β = 1.0 (default: α=0.7, β=0.3)
```

---

## 🗄️ The Two Databases

### Neo4j Graph Schema

```mermaid
graph LR
    D1[(Document 1)]
    D2[(Document 2)]
    E1((Entity: Einstein))
    E2((Entity: Germany))
    
    D1 -->|MENTIONS| E1
    D1 -->|MENTIONS| E2
    D2 -->|MENTIONS| E1
    D1 -.->|RELATED_TO<br/>weight: 0.87| D2
    
    style D1 fill:#b3d9ff
    style D2 fill:#b3d9ff
    style E1 fill:#ffb3b3
    style E2 fill:#ffb3b3
```

**What Neo4j stores:**

| Node Type | Properties | Purpose |
|-----------|-----------|----------|
| **Document** | id, text, title, vector_id | Stores content |
| **Entity** | name, type (PERSON, ORG, GPE, DATE) | Extracted info |

**Relationship Types:**
- `MENTIONS`: Document → Entity
- `RELATED_TO`: Document → Document (semantic similarity)

### FAISS Vector Index

**What FAISS stores:**
- Document embeddings (384-dimensional vectors)
- ID mappings (vector ID → document ID)

**Configuration:**
- **Index Type**: `IndexFlatIP` (Inner Product / Cosine Similarity)
- **Dimension**: 384 (from `all-MiniLM-L6-v2`)
- **Storage**: `data/faiss_index.bin` + `data/faiss_map.pkl`

**How it works:**
```
Document "Einstein was a physicist" 
              │
              ▼ Embedding Model
[0.23, -0.15, 0.87, ..., 0.42]  ← 384 numbers
              │
              ▼ Stored in FAISS
              
When searching, find closest vectors
using cosine similarity
```

---

## 🔗 How Components Connect - Request Flow

Here's what happens when you make a search request:

```mermaid
flowchart TD
    A[🌐 HTTP Request<br/>POST /v1/search/vector] --> B[📍 Route: search.py]
    
    B --> |"Validates input"| C[🎮 Controller: SearchController]
    
    C --> |"Encode query"| D[🔧 Service: EmbeddingService]
    D --> |"384-dim vector"| C
    
    C --> E[📦 Repository: VectorRepository]
    C --> F[📦 Repository: Neo4jRepository]
    
    E --> |"Search vectors"| G[(FAISS Index)]
    F --> |"Fetch documents"| H[(Neo4j DB)]
    
    G --> |"distances, indices"| E
    H --> |"document data"| F
    
    E --> C
    F --> C
    
    C --> |"Format results"| B
    B --> I[📤 JSON Response]
    
    style A fill:#e1f5ff
    style I fill:#e1ffe1
    style G fill:#ffe1e1
    style H fill:#ffe1e1
```

**Summary:**
1. **Route** receives and validates the HTTP request
2. **Controller** orchestrates the business logic
3. **Service** handles text-to-vector conversion
4. **Repositories** talk to their respective databases
5. **Response** returns formatted JSON to the client

---

## 🛡️ Error Handling

The system uses **custom exceptions** for clean error handling:

```mermaid
graph TD
    A[BaseAPIException] --> B[NodeNotFoundError<br/>404]
    A --> C[EdgeCreationError<br/>400]
    A --> D[IngestionError<br/>500]
    A --> E[SearchError<br/>500]
    A --> F[ValidationError<br/>422]
    
    B --- B1[Document ID doesn't exist]
    C --- C1[Relationship creation failed]
    D --- D1[Document processing failed]
    E --- E1[Search operation failed]
    F --- F1[Invalid input data]
    
    style A fill:#ffcccc
    style B fill:#ffe6cc
    style C fill:#ffe6cc
    style D fill:#ffe6cc
    style E fill:#ffe6cc
    style F fill:#ffe6cc
```

**Benefits:**
- ✅ Proper HTTP status codes for each error type
- ✅ Consistent error response format
- ✅ No stack traces exposed to clients
- ✅ Detailed server-side logging

---

## 🔑 Key Concepts Summary

| Concept | What It Is | Why It Matters |
|---------|-----------|----------------|
| **Embedding** | Text converted to numbers (vector) | Enables semantic comparison |
| **Vector Search** | Finding similar embeddings | Understands meaning |
| **Graph Traversal** | Following connections | Finds related content |
| **Hybrid Search** | Combining both approaches | Best of both worlds |
| **Entity Extraction** | Finding names, places, dates | Builds knowledge graph |
| **Semantic Edges** | Auto-created relationships | Connects similar docs |

---

## 🎓 Quick Reference: API Endpoints

| Endpoint | Method | What It Does |
|----------|--------|-------------|
| `/v1/health` | GET | Check if system is running |
| `/v1/nodes` | POST | Create a new document |
| `/v1/nodes/{id}` | GET | Get a document by ID |
| `/v1/nodes/{id}` | PUT | Update a document |
| `/v1/nodes/{id}` | DELETE | Delete a document |
| `/v1/edges` | POST | Create a relationship |
| `/v1/search/vector` | POST | Semantic search |
| `/v1/search/graph` | GET | Graph traversal |
| `/v1/search/hybrid` | POST | Combined search |

---

## 🎯 TL;DR (Too Long; Didn't Read)

1. **Frontend** talks to **Backend** via REST API
2. **Backend** has 4 layers: Routes → Controllers → Repositories → Databases
3. **Two databases**: Neo4j (relationships) + FAISS (similarity)
4. **Documents get processed**: cleaned → chunked → embedded → stored → connected
5. **Three search modes**: Vector (semantic), Graph (structural), Hybrid (best of both)

---

## 📚 Next Steps

- **README.md**: Setup instructions and usage examples
- **ARCHITECTURE.md**: Deep technical details with code
- **Interactive API Docs**: Visit `http://localhost:8000/docs` when running

---

*Built with FastAPI, Neo4j, FAISS, and ❤️*
