"""Application-wide constants and configuration values"""

# Edge type whitelist - prevents Cypher injection
ALLOWED_EDGE_TYPES = {
    "RELATED_TO",
    "MENTIONS",
    "CONTAINS",
    "PART_OF",
    "BELONGS_TO",
    "REFERENCES"
}

# Entity types from spaCy NER
ALLOWED_ENTITY_TYPES = {
    "ORG",       # Organizations
    "PERSON",    # People
    "GPE",       # Geopolitical entities (countries, cities)
    "DATE",      # Dates
    "LOC",       # Locations
    "PRODUCT",   # Products
    "EVENT"      # Named events
}

# Search configuration
MAX_SEARCH_RESULTS = 100
DEFAULT_SEARCH_TOP_K = 10
MAX_GRAPH_DEPTH = 5
DEFAULT_GRAPH_DEPTH = 2

# Ingestion configuration
DEFAULT_CHUNK_SIZE = 256
DEFAULT_CHUNK_OVERLAP = 12
MAX_CHUNK_SIZE = 1024
SEMANTIC_EDGE_SIMILARITY_THRESHOLD = 0.85
MAX_SEMANTIC_NEIGHBORS = 5

# Vector search configuration
VECTOR_SEARCH_MULTIPLIER = 3  # Fetch 3x results for hybrid search

# Graph scoring parameters
DEFAULT_VECTOR_WEIGHT = 0.7
DEFAULT_GRAPH_WEIGHT = 0.3
