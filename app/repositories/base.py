# File: app/repositories/base.py
"""Base repository interface"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseRepository(ABC):
    """Abstract base class for all repositories"""
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Any:
        """Create a new entity"""
        pass
    
    @abstractmethod
    def get(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an entity by ID"""
        pass
    
    @abstractmethod
    def update(self, entity_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing entity"""
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity"""
        pass
