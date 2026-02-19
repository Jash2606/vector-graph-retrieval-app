"""Custom exception classes for better error handling"""


class BaseAPIException(Exception):
    """Base exception for all API errors"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DocumentNotFoundError(BaseAPIException):
    """Raised when a document is not found"""

    def __init__(self, doc_id: str):
        super().__init__(
            f"Document with ID '{doc_id}' not found",
            status_code=404)
        self.doc_id = doc_id


class NodeNotFoundError(BaseAPIException):
    """Raised when a node is not found in the graph"""

    def __init__(self, node_id: str):
        super().__init__(
            f"Node with ID '{node_id}' not found",
            status_code=404)
        self.node_id = node_id


class EdgeCreationError(BaseAPIException):
    """Raised when edge creation fails"""

    def __init__(self, source_id: str, target_id: str, reason: str = ""):
        message = f"Failed to create edge from '{source_id}' to '{target_id}'"
        if reason:
            message += f": {reason}"
        super().__init__(message, status_code=400)


class InvalidEdgeTypeError(BaseAPIException):
    """Raised when an invalid edge type is provided"""

    def __init__(self, edge_type: str, allowed_types: list):
        super().__init__(
            f"Invalid edge type '{edge_type}'. Allowed types: {
                ', '.join(allowed_types)}",
            status_code=400)


class IngestionError(BaseAPIException):
    """Raised when document ingestion fails"""

    def __init__(self, reason: str):
        super().__init__(
            f"Document ingestion failed: {reason}",
            status_code=500)


class SearchError(BaseAPIException):
    """Raised when search operation fails"""

    def __init__(self, reason: str):
        super().__init__(f"Search operation failed: {reason}", status_code=500)


class DatabaseConnectionError(BaseAPIException):
    """Raised when database connection fails"""

    def __init__(self, db_name: str, reason: str = ""):
        message = f"Failed to connect to {db_name}"
        if reason:
            message += f": {reason}"
        super().__init__(message, status_code=503)


class ValidationError(BaseAPIException):
    """Raised when input validation fails"""

    def __init__(self, field: str, reason: str):
        super().__init__(
            f"Validation error for '{field}': {reason}",
            status_code=422)
