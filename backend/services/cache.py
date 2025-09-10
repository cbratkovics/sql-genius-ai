import redis.asyncio as redis
import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)


class IntelligentCache:
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False  # We'll handle encoding ourselves
        )
        self.default_ttl = 3600  # 1 hour
        
    async def get(self, key: str) -> Optional[Any]:
        try:
            data = await self.redis_client.get(key)
            if data is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            # Try to serialize as JSON first, then pickle
            try:
                data = json.dumps(value, default=str).encode('utf-8')
            except (TypeError, ValueError):
                data = pickle.dumps(value)
            
            await self.redis_client.setex(key, ttl, data)
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache exists check failed for key {key}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache pattern invalidation failed for {pattern}: {e}")
            return 0
    
    def create_query_cache_key(
        self, 
        user_id: str, 
        query_hash: str, 
        schema_hash: str
    ) -> str:
        return f"query:{user_id}:{query_hash}:{schema_hash}"
    
    def create_result_cache_key(self, query_id: str) -> str:
        return f"result:{query_id}"
    
    def create_schema_cache_key(self, file_id: str) -> str:
        return f"schema:{file_id}"
    
    def create_semantic_cache_key(self, query_embedding: str) -> str:
        return f"semantic:{query_embedding}"
    
    async def get_similar_queries(
        self, 
        query_text: str, 
        tenant_id: str, 
        similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Find semantically similar cached queries"""
        try:
            # Create a simple hash-based similarity check
            # In production, you'd use vector embeddings
            query_hash = hashlib.md5(query_text.lower().encode()).hexdigest()
            pattern = f"query:{tenant_id}:*"
            
            keys = await self.redis_client.keys(pattern)
            similar_queries = []
            
            for key in keys:
                cached_data = await self.get(key)
                if cached_data and 'query_text' in cached_data:
                    # Simple similarity check (would use embeddings in production)
                    cached_hash = hashlib.md5(
                        cached_data['query_text'].lower().encode()
                    ).hexdigest()
                    
                    # Calculate simple similarity (Hamming distance)
                    similarity = sum(
                        a == b for a, b in zip(query_hash, cached_hash)
                    ) / len(query_hash)
                    
                    if similarity >= similarity_threshold:
                        similar_queries.append({
                            'key': key,
                            'similarity': similarity,
                            'data': cached_data
                        })
            
            return sorted(similar_queries, key=lambda x: x['similarity'], reverse=True)
            
        except Exception as e:
            logger.error(f"Similar query search failed: {e}")
            return []
    
    async def cache_query_result(
        self,
        query_id: str,
        result_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache query results with intelligent TTL based on data volatility"""
        try:
            # Determine TTL based on data characteristics
            if ttl is None:
                ttl = self._calculate_intelligent_ttl(result_data)
            
            cache_key = self.create_result_cache_key(query_id)
            return await self.set(cache_key, result_data, ttl)
            
        except Exception as e:
            logger.error(f"Query result caching failed: {e}")
            return False
    
    def _calculate_intelligent_ttl(self, result_data: Dict[str, Any]) -> int:
        """Calculate TTL based on data characteristics"""
        base_ttl = 3600  # 1 hour
        
        # Adjust based on result size
        result_size = len(str(result_data))
        if result_size > 100000:  # Large results cache longer
            base_ttl *= 2
        
        # Adjust based on data type
        if 'aggregation' in result_data.get('query_type', ''):
            base_ttl *= 3  # Aggregations change less frequently
        
        if 'real_time' in result_data.get('tags', []):
            base_ttl = 300  # 5 minutes for real-time data
        
        return base_ttl
    
    async def warm_cache(
        self, 
        popular_queries: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """Pre-populate cache with popular queries"""
        results = {}
        
        for query_info in popular_queries:
            try:
                cache_key = query_info['cache_key']
                data = query_info['data']
                ttl = query_info.get('ttl', self.default_ttl)
                
                success = await self.set(cache_key, data, ttl)
                results[cache_key] = success
                
            except Exception as e:
                logger.error(f"Cache warming failed for query: {e}")
                results[query_info.get('cache_key', 'unknown')] = False
        
        return results
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            info = await self.redis_client.info()
            
            return {
                'memory_usage': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        total = hits + misses
        if total == 0:
            return 0.0
        return hits / total
    
    async def close(self):
        """Close Redis connection"""
        await self.redis_client.close()


cache_service = IntelligentCache()