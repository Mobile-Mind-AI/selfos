"""
Enhanced Vector Memory Service

Advanced memory service with multiple vector database backends,
semantic search, and AI-powered memory retrieval.
"""

import logging
import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class VectorStoreType(Enum):
    """Supported vector store types."""
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    CHROMA = "chroma"
    LOCAL_FAISS = "local_faiss"
    MEMORY = "memory"  # In-memory for development


@dataclass
class MemoryEntry:
    """Structured memory entry."""
    id: str
    user_id: str
    content: str
    content_type: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: datetime = None
    relevance_score: float = 0.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class SearchResult:
    """Memory search result."""
    entry: MemoryEntry
    similarity_score: float
    context_relevance: float
    
    @property
    def combined_score(self) -> float:
        """Combined relevance score."""
        return (self.similarity_score * 0.7) + (self.context_relevance * 0.3)


class EmbeddingProvider:
    """Abstract base for embedding providers."""
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        raise NotImplementedError
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        raise NotImplementedError


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("OpenAI package not installed")
        return self._client
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI."""
        client = self._get_client()
        
        try:
            response = await client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return 1536  # ada-002 dimension


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local embedding provider using sentence-transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
    
    def _get_model(self):
        """Lazy load sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError("sentence-transformers package not installed")
        return self._model
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using local model."""
        model = self._get_model()
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, 
            lambda: model.encode([text])[0].tolist()
        )
        return embedding
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return 384  # MiniLM dimension


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for development."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate mock embedding."""
        import random
        import hashlib
        
        # Generate deterministic embedding based on text hash
        text_hash = hashlib.md5(text.encode()).hexdigest()
        random.seed(text_hash)
        
        return [random.uniform(-1, 1) for _ in range(self.dimension)]
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


class VectorStore:
    """Abstract base for vector stores."""
    
    async def upsert(self, entries: List[MemoryEntry]) -> bool:
        """Insert or update memory entries."""
        raise NotImplementedError
    
    async def search(
        self, 
        query_embedding: List[float], 
        user_id: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search for similar entries."""
        raise NotImplementedError
    
    async def delete(self, entry_ids: List[str], user_id: str) -> bool:
        """Delete entries."""
        raise NotImplementedError
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get storage statistics."""
        raise NotImplementedError


class PineconeVectorStore(VectorStore):
    """Pinecone vector store implementation."""
    
    def __init__(self, api_key: str, environment: str, index_name: str):
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self._index = None
    
    def _get_index(self):
        """Lazy load Pinecone index."""
        if self._index is None:
            try:
                import pinecone
                pinecone.init(api_key=self.api_key, environment=self.environment)
                self._index = pinecone.Index(self.index_name)
            except ImportError:
                raise ImportError("pinecone-client package not installed")
        return self._index
    
    async def upsert(self, entries: List[MemoryEntry]) -> bool:
        """Upsert entries to Pinecone."""
        index = self._get_index()
        
        try:
            vectors = []
            for entry in entries:
                if entry.embedding:
                    vectors.append({
                        "id": entry.id,
                        "values": entry.embedding,
                        "metadata": {
                            **entry.metadata,
                            "user_id": entry.user_id,
                            "content": entry.content[:1000],  # Pinecone metadata limit
                            "content_type": entry.content_type,
                            "created_at": entry.created_at.isoformat()
                        }
                    })
            
            if vectors:
                index.upsert(vectors=vectors)
                logger.info(f"Upserted {len(vectors)} vectors to Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"Pinecone upsert error: {e}")
            return False
    
    async def search(
        self, 
        query_embedding: List[float], 
        user_id: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search Pinecone index."""
        index = self._get_index()
        
        try:
            # Build filter
            filter_dict = {"user_id": {"$eq": user_id}}
            if filters:
                filter_dict.update(filters)
            
            response = index.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True,
                filter=filter_dict
            )
            
            results = []
            for match in response["matches"]:
                metadata = match["metadata"]
                entry = MemoryEntry(
                    id=match["id"],
                    user_id=metadata["user_id"],
                    content=metadata["content"],
                    content_type=metadata["content_type"],
                    metadata=metadata,
                    created_at=datetime.fromisoformat(metadata["created_at"])
                )
                
                result = SearchResult(
                    entry=entry,
                    similarity_score=match["score"],
                    context_relevance=1.0  # Would calculate based on filters
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Pinecone search error: {e}")
            return []
    
    async def delete(self, entry_ids: List[str], user_id: str) -> bool:
        """Delete entries from Pinecone."""
        index = self._get_index()
        
        try:
            index.delete(ids=entry_ids, filter={"user_id": {"$eq": user_id}})
            return True
        except Exception as e:
            logger.error(f"Pinecone delete error: {e}")
            return False
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get Pinecone statistics."""
        index = self._get_index()
        
        try:
            stats = index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
        except Exception as e:
            logger.error(f"Pinecone stats error: {e}")
            return {}


class InMemoryVectorStore(VectorStore):
    """In-memory vector store for development and testing."""
    
    def __init__(self):
        self.entries: Dict[str, MemoryEntry] = {}
        self._lock = asyncio.Lock()
    
    async def upsert(self, entries: List[MemoryEntry]) -> bool:
        """Store entries in memory."""
        async with self._lock:
            for entry in entries:
                self.entries[entry.id] = entry
            logger.debug(f"Stored {len(entries)} entries in memory")
            return True
    
    async def search(
        self, 
        query_embedding: List[float], 
        user_id: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Search entries using cosine similarity."""
        async with self._lock:
            results = []
            
            for entry in self.entries.values():
                if entry.user_id != user_id:
                    continue
                
                if not entry.embedding:
                    continue
                
                # Apply filters
                if filters:
                    if not self._apply_filters(entry, filters):
                        continue
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                
                result = SearchResult(
                    entry=entry,
                    similarity_score=similarity,
                    context_relevance=1.0
                )
                results.append(result)
            
            # Sort by combined score and limit
            results.sort(key=lambda x: x.combined_score, reverse=True)
            return results[:limit]
    
    def _apply_filters(self, entry: MemoryEntry, filters: Dict[str, Any]) -> bool:
        """Apply search filters to entry."""
        for key, value in filters.items():
            if key in entry.metadata:
                if entry.metadata[key] != value:
                    return False
            elif hasattr(entry, key):
                if getattr(entry, key) != value:
                    return False
        return True
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors."""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def delete(self, entry_ids: List[str], user_id: str) -> bool:
        """Delete entries from memory."""
        async with self._lock:
            deleted = 0
            for entry_id in entry_ids:
                if entry_id in self.entries and self.entries[entry_id].user_id == user_id:
                    del self.entries[entry_id]
                    deleted += 1
            
            logger.debug(f"Deleted {deleted} entries from memory")
            return True
    
    async def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory store statistics."""
        async with self._lock:
            user_entries = [e for e in self.entries.values() if e.user_id == user_id]
            
            return {
                "total_entries": len(user_entries),
                "content_types": list(set(e.content_type for e in user_entries)),
                "oldest_entry": min(e.created_at for e in user_entries) if user_entries else None,
                "newest_entry": max(e.created_at for e in user_entries) if user_entries else None
            }


class EnhancedMemoryService:
    """Enhanced memory service with vector search capabilities."""
    
    def __init__(
        self,
        vector_store_type: VectorStoreType = VectorStoreType.MEMORY,
        embedding_provider: Optional[EmbeddingProvider] = None,
        **kwargs
    ):
        self.vector_store_type = vector_store_type
        self.embedding_provider = embedding_provider or self._create_default_embedding_provider()
        self.vector_store = self._create_vector_store(**kwargs)
        self.config = self._load_config()
    
    def _create_default_embedding_provider(self) -> EmbeddingProvider:
        """Create default embedding provider."""
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            return OpenAIEmbeddingProvider(openai_key)
        else:
            return MockEmbeddingProvider()
    
    def _create_vector_store(self, **kwargs) -> VectorStore:
        """Create vector store based on type."""
        if self.vector_store_type == VectorStoreType.PINECONE:
            return PineconeVectorStore(
                api_key=kwargs.get("pinecone_api_key", os.getenv("PINECONE_API_KEY")),
                environment=kwargs.get("pinecone_env", os.getenv("PINECONE_ENVIRONMENT")),
                index_name=kwargs.get("pinecone_index", os.getenv("PINECONE_INDEX", "selfos"))
            )
        elif self.vector_store_type == VectorStoreType.MEMORY:
            return InMemoryVectorStore()
        else:
            raise ValueError(f"Unsupported vector store type: {self.vector_store_type}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load memory service configuration."""
        return {
            "similarity_threshold": float(os.getenv("MEMORY_SIMILARITY_THRESHOLD", "0.7")),
            "max_content_length": int(os.getenv("MEMORY_MAX_CONTENT_LENGTH", "2000")),
            "retention_days": int(os.getenv("MEMORY_RETENTION_DAYS", "365")),
            "enable_content_filtering": os.getenv("MEMORY_ENABLE_FILTERING", "true").lower() == "true"
        }
    
    async def store_memory(
        self,
        user_id: str,
        content: str,
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a new memory entry."""
        try:
            # Generate unique ID
            entry_id = self._generate_entry_id(user_id, content, content_type)
            
            # Prepare content
            clean_content = self._clean_content(content)
            
            # Generate embedding
            embedding = await self.embedding_provider.generate_embedding(clean_content)
            
            # Create memory entry
            entry = MemoryEntry(
                id=entry_id,
                user_id=user_id,
                content=clean_content,
                content_type=content_type,
                metadata=metadata or {},
                embedding=embedding
            )
            
            # Store in vector database
            success = await self.vector_store.upsert([entry])
            
            if success:
                logger.info(f"Stored memory entry {entry_id} for user {user_id}")
                return entry_id
            else:
                raise Exception("Failed to store in vector database")
                
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        content_types: Optional[List[str]] = None,
        limit: int = 10,
        min_similarity: Optional[float] = None
    ) -> List[SearchResult]:
        """Search for relevant memories."""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_provider.generate_embedding(query)
            
            # Build filters
            filters = {}
            if content_types:
                filters["content_type"] = {"$in": content_types}
            
            # Search vector store
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                user_id=user_id,
                limit=limit * 2,  # Get more then filter
                filters=filters
            )
            
            # Apply similarity threshold
            threshold = min_similarity or self.config["similarity_threshold"]
            filtered_results = [
                result for result in results 
                if result.similarity_score >= threshold
            ]
            
            # Enhance with context relevance
            enhanced_results = await self._enhance_context_relevance(filtered_results, query)
            
            return enhanced_results[:limit]
            
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return []
    
    async def get_recent_memories(
        self,
        user_id: str,
        content_types: Optional[List[str]] = None,
        limit: int = 10,
        days_back: int = 30
    ) -> List[MemoryEntry]:
        """Get recent memories for context."""
        # This would be implemented with time-based filtering
        # For now, return empty list as placeholder
        return []
    
    async def delete_memories(
        self,
        user_id: str,
        entry_ids: Optional[List[str]] = None,
        older_than_days: Optional[int] = None
    ) -> int:
        """Delete memories by IDs or age."""
        try:
            if entry_ids:
                success = await self.vector_store.delete(entry_ids, user_id)
                return len(entry_ids) if success else 0
            
            if older_than_days:
                # Would implement age-based deletion
                logger.warning("Age-based deletion not yet implemented")
                return 0
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to delete memories: {e}")
            return 0
    
    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for user."""
        try:
            stats = await self.vector_store.get_stats(user_id)
            
            stats.update({
                "vector_store_type": self.vector_store_type.value,
                "embedding_dimension": self.embedding_provider.get_dimension(),
                "similarity_threshold": self.config["similarity_threshold"]
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    
    def _generate_entry_id(self, user_id: str, content: str, content_type: str) -> str:
        """Generate unique entry ID."""
        import uuid
        timestamp = datetime.utcnow().isoformat()
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{user_id}_{content_type}_{timestamp}_{content_hash}_{uuid.uuid4().hex[:8]}"
    
    def _clean_content(self, content: str) -> str:
        """Clean and prepare content for embedding."""
        # Remove excessive whitespace
        import re
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Truncate if too long
        max_length = self.config["max_content_length"]
        if len(content) > max_length:
            content = content[:max_length - 3] + "..."
        
        return content
    
    async def _enhance_context_relevance(
        self, 
        results: List[SearchResult], 
        query: str
    ) -> List[SearchResult]:
        """Enhance results with context relevance scoring."""
        # Simple enhancement - in production would use more sophisticated scoring
        for result in results:
            # Boost recent memories
            age_days = (datetime.utcnow() - result.entry.created_at).days
            recency_boost = max(0, 1 - (age_days / 30))  # Decay over 30 days
            
            # Boost certain content types for certain queries
            content_type_boost = 1.0
            if "task" in query.lower() and result.entry.content_type == "task_completion":
                content_type_boost = 1.2
            
            result.context_relevance = recency_boost * content_type_boost
        
        # Sort by combined score
        results.sort(key=lambda x: x.combined_score, reverse=True)
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of memory service."""
        health = {
            "status": "healthy",
            "vector_store": self.vector_store_type.value,
            "embedding_provider": type(self.embedding_provider).__name__
        }
        
        try:
            # Test embedding generation
            test_embedding = await self.embedding_provider.generate_embedding("test")
            health["embedding_dimension"] = len(test_embedding)
            
            # Test vector store (if possible)
            stats = await self.vector_store.get_stats("health_check")
            health["vector_store_accessible"] = True
            
        except Exception as e:
            health["status"] = "degraded"
            health["error"] = str(e)
        
        return health


# Factory function for easy initialization
def create_memory_service(
    vector_store_type: str = "memory",
    **kwargs
) -> EnhancedMemoryService:
    """Create memory service with specified configuration."""
    store_type = VectorStoreType(vector_store_type.lower())
    
    return EnhancedMemoryService(
        vector_store_type=store_type,
        **kwargs
    )