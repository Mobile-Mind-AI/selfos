"""
Vector Memory Service

This service handles indexing tasks and content into a vector database
for semantic search and AI memory capabilities.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Configuration for vector database
VECTOR_DB_CONFIG = {
    "collection_name": "selfos_memories",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",  # Default model
    "vector_dimension": 384,  # Dimension for the default model
    "similarity_threshold": 0.7
}

async def index_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Index a completed task into the vector database for semantic memory.
    
    Args:
        task_data: Task information from completion event
        
    Returns:
        Dict with indexing results
    """
    try:
        task_id = task_data.get("task_id")
        user_id = task_data.get("user_id")
        
        # Prepare content for embedding
        content = await _prepare_task_content(task_data)
        
        # Generate embedding (simplified - in production would use actual embedding model)
        embedding = await _generate_embedding(content["text"])
        
        # Prepare metadata
        metadata = {
            "user_id": user_id,
            "task_id": task_id,
            "content_type": "task_completion",
            "title": task_data.get("title", ""),
            "goal_id": task_data.get("goal_id"),
            "life_area_id": task_data.get("life_area_id"),
            "completion_date": datetime.utcnow().isoformat(),
            "has_media": task_data.get("media_count", 0) > 0,
            "duration_minutes": task_data.get("duration"),
            "tags": content["tags"]
        }
        
        # Store in vector database
        vector_id = await _store_in_vector_db(
            content=content["text"],
            embedding=embedding,
            metadata=metadata
        )
        
        logger.info(f"Indexed task {task_id} into vector memory as {vector_id}")
        
        return {
            "success": True,
            "vector_id": vector_id,
            "content_length": len(content["text"]),
            "tags": content["tags"],
            "indexed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to index task: {e}")
        return {"success": False, "error": str(e)}

async def _prepare_task_content(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare task content for vector embedding.
    
    Args:
        task_data: Raw task data
        
    Returns:
        Dict with processed content and metadata
    """
    title = task_data.get("title", "")
    description = task_data.get("description", "")
    
    # Build comprehensive content string
    content_parts = [f"Task: {title}"]
    
    if description:
        content_parts.append(f"Description: {description}")
    
    # Add context about completion
    content_parts.append("Status: Completed successfully")
    
    if task_data.get("duration"):
        duration = task_data["duration"]
        hours = duration // 60
        minutes = duration % 60
        if hours > 0:
            content_parts.append(f"Duration: {hours} hours {minutes} minutes")
        else:
            content_parts.append(f"Duration: {minutes} minutes")
    
    if task_data.get("media_count", 0) > 0:
        content_parts.append(f"Documented with {task_data['media_count']} media attachments")
    
    # Generate tags for categorization
    tags = []
    
    # Add duration-based tags
    if task_data.get("duration"):
        duration = task_data["duration"]
        if duration < 30:
            tags.append("quick-task")
        elif duration < 120:
            tags.append("medium-task")
        else:
            tags.append("long-task")
    
    # Add media-based tags
    if task_data.get("media_count", 0) > 0:
        tags.append("documented")
    
    # Add content-based tags (simple keyword extraction)
    text_content = f"{title} {description}".lower()
    
    keyword_tags = {
        "learning": ["learn", "study", "course", "skill", "practice"],
        "health": ["exercise", "workout", "health", "fitness", "run", "gym"],
        "work": ["work", "project", "meeting", "deadline", "client"],
        "creative": ["create", "design", "write", "art", "music", "photo"],
        "social": ["friend", "family", "social", "meet", "call", "visit"],
        "maintenance": ["clean", "organize", "fix", "repair", "maintain"]
    }
    
    for tag, keywords in keyword_tags.items():
        if any(keyword in text_content for keyword in keywords):
            tags.append(tag)
    
    content_text = ". ".join(content_parts)
    
    return {
        "text": content_text,
        "tags": tags,
        "word_count": len(content_text.split())
    }

async def _generate_embedding(text: str) -> List[float]:
    """
    Generate vector embedding for text content.
    
    In production, this would use a real embedding model like:
    - sentence-transformers
    - OpenAI embeddings API
    - Cohere embeddings
    - Local transformer models
    
    For now, returns a mock embedding.
    """
    try:
        # Mock embedding generation
        # In production, would look like:
        # from sentence_transformers import SentenceTransformer
        # model = SentenceTransformer('all-MiniLM-L6-v2')
        # embedding = model.encode(text).tolist()
        
        # Create a deterministic mock embedding based on text content
        import hashlib
        hash_object = hashlib.md5(text.encode())
        hex_dig = hash_object.hexdigest()
        
        # Convert hash to float values (mock embedding)
        mock_embedding = []
        for i in range(0, min(len(hex_dig), 32), 2):  # Take pairs of hex chars
            hex_pair = hex_dig[i:i+2]
            # Convert to float between -1 and 1
            value = (int(hex_pair, 16) / 255.0) * 2 - 1
            mock_embedding.append(value)
        
        # Pad to desired dimension
        while len(mock_embedding) < VECTOR_DB_CONFIG["vector_dimension"]:
            mock_embedding.extend(mock_embedding[:min(len(mock_embedding), 
                                                     VECTOR_DB_CONFIG["vector_dimension"] - len(mock_embedding))])
        
        return mock_embedding[:VECTOR_DB_CONFIG["vector_dimension"]]
        
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        # Return zero vector as fallback
        return [0.0] * VECTOR_DB_CONFIG["vector_dimension"]

async def _store_in_vector_db(content: str, embedding: List[float], metadata: Dict[str, Any]) -> str:
    """
    Store content and embedding in vector database.
    
    In production, this would integrate with:
    - Weaviate
    - Pinecone
    - Chroma
    - FAISS
    - Qdrant
    
    For now, simulates storage.
    """
    try:
        # Generate unique ID for this vector
        vector_id = f"vec_{metadata['user_id']}_{metadata['task_id']}_{int(datetime.utcnow().timestamp())}"
        
        # In production, would store in actual vector database:
        # weaviate_client.data_object.create(
        #     data_object={
        #         "content": content,
        #         "metadata": metadata
        #     },
        #     class_name=VECTOR_DB_CONFIG["collection_name"],
        #     vector=embedding,
        #     uuid=vector_id
        # )
        
        # For now, just log the storage
        logger.info(f"[VECTOR_DB] Stored {vector_id}: {content[:100]}... with {len(embedding)}D embedding")
        
        return vector_id
        
    except Exception as e:
        logger.error(f"Failed to store in vector database: {e}")
        raise

async def search_memories(user_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search user's memory using semantic similarity.
    
    Args:
        user_id: ID of the user
        query: Search query
        limit: Maximum number of results
        
    Returns:
        List of matching memories with similarity scores
    """
    try:
        # Generate embedding for query
        query_embedding = await _generate_embedding(query)
        
        # In production, would perform vector similarity search:
        # results = weaviate_client.query.get(
        #     class_name=VECTOR_DB_CONFIG["collection_name"],
        #     properties=["content", "metadata"],
        # ).with_where({
        #     "path": ["metadata", "user_id"],
        #     "operator": "Equal",
        #     "valueString": user_id
        # }).with_near_vector({
        #     "vector": query_embedding
        # }).with_limit(limit).do()
        
        # Mock search results
        mock_results = [
            {
                "content": f"Mock memory result for query: {query}",
                "metadata": {
                    "user_id": user_id,
                    "task_id": "123",
                    "title": "Related task",
                    "completion_date": datetime.utcnow().isoformat(),
                    "tags": ["mock", "example"]
                },
                "similarity_score": 0.85
            }
        ]
        
        logger.info(f"Memory search for user {user_id}: '{query}' returned {len(mock_results)} results")
        
        return mock_results
        
    except Exception as e:
        logger.error(f"Failed to search memories: {e}")
        return []

async def get_user_memory_stats(user_id: str) -> Dict[str, Any]:
    """
    Get statistics about user's indexed memories.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dict with memory statistics
    """
    try:
        # In production, would query vector database for user's data
        # count_result = weaviate_client.query.aggregate(
        #     class_name=VECTOR_DB_CONFIG["collection_name"]
        # ).with_where({
        #     "path": ["metadata", "user_id"],
        #     "operator": "Equal",
        #     "valueString": user_id
        # }).with_fields("meta { count }").do()
        
        # Mock statistics
        stats = {
            "total_memories": 42,  # Mock count
            "indexed_tasks": 35,
            "indexed_goals": 7,
            "total_content_words": 2450,
            "most_common_tags": ["work", "learning", "health"],
            "last_indexed": datetime.utcnow().isoformat(),
            "memory_health": "good"
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        return {"error": str(e)}

async def suggest_related_tasks(user_id: str, current_task_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Suggest related tasks based on semantic similarity.
    
    Args:
        user_id: ID of the user
        current_task_data: Current task being worked on
        
    Returns:
        List of related task suggestions
    """
    try:
        # Prepare current task content for search
        content = await _prepare_task_content(current_task_data)
        
        # Search for similar memories
        similar_memories = await search_memories(user_id, content["text"], limit=5)
        
        # Convert to task suggestions
        suggestions = []
        for memory in similar_memories:
            if memory["similarity_score"] > VECTOR_DB_CONFIG["similarity_threshold"]:
                suggestions.append({
                    "related_task_id": memory["metadata"]["task_id"],
                    "title": memory["metadata"]["title"],
                    "similarity_score": memory["similarity_score"],
                    "reason": "semantic_similarity",
                    "shared_tags": list(set(content["tags"]) & set(memory["metadata"]["tags"]))
                })
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Failed to suggest related tasks: {e}")
        return []