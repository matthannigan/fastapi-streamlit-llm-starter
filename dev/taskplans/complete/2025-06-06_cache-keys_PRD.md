# FastAPI-Streamlit-LLM Starter Template

A production-ready starter template for building AI-powered applications using FastAPI, Streamlit, and PydanticAI.

## 🌟 Features

- **🚀 Modern Stack**: FastAPI + Streamlit + PydanticAI
- **🤖 AI Integration**: Easy integration with multiple AI models
- **📊 Rich UI**: Interactive Streamlit interface with real-time updates
- **🐳 Docker Ready**: Complete containerization for easy deployment
- **🔒 Production Ready**: Security headers, rate limiting, health checks
- **📈 Scalable**: Designed for horizontal scaling
- **🧪 Extensible**: Easy to add new features and AI operations

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │───▶│     FastAPI      │───▶│   PydanticAI    │
│   Frontend      │    │     Backend      │    │   + LLM APIs    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                      │
         │              ┌─────────────────┐             │
         └─────────────▶│  Shared Models  │◀────────────┘
                        │   (Pydantic)    │
                        └─────────────────┘
```

### Project Structure (Abbreviated)

```
fastapi-streamlit-llm-starter/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py                     # FastAPI app and main routes
│   │   ├── config.py                   # Configuration management
│   │   ├── auth.py                     # Authentication and authorization
│   │   ├── dependencies.py             # Dependency injection
│   │   ├── resilience_endpoints.py     # Resilience testing endpoints
│   │   ├── services/                   # Business logic services
│   │   │   ├── cache.py                    # Redis caching service
│   │   │   ├── text_processor.py           # AI text processing service
│   │   │   ├── prompt_builder.py           # Prompt construction utilities
│   │   │   └── resilience.py               # System resilience testing
│   │   ├── security/                   # Security components
│   │   │   └── response_validator.py       # API response validation
│   │   ├── utils/                      # Utility functions
│   │   │   ├── prompt_utils.py             # Prompt helper functions
│   │   │   └── sanitization.py             # Input sanitization
│   │   └── __init__.py
│   ├── tests/                      # Comprehensive unit tests
│   ├── requirements.txt            # Production dependencies
│   ├── requirements-dev.txt        # Development dependencies
│   ├── requirements.docker.txt     # Docker-specific dependencies
│   ├── pytest.ini                  # Test configuration
│   ├── Dockerfile                  # Container configuration
│   ├── .dockerignore               # Docker ignore patterns
│   └── README.md                   # Backend documentation
├── frontend/                   # Streamlit application
│   ├── app/
│   │   ├── app.py                      # Main Streamlit app
│   │   ├── config.py                   # Frontend configuration
│   │   └── utils/                      # Utility functions
│   ├── tests/                      # Unit tests for frontend
│   ├── requirements.txt            # Production dependencies
│   ├── requirements-dev.txt        # Development dependencies
│   ├── requirements.docker.txt     # Docker-specific dependencies
│   ├── pytest.ini                  # Test configuration
│   ├── Dockerfile                  # Container configuration
│   ├── .dockerignore               # Docker ignore patterns
│   └── README.md                   # Frontend documentation
├── shared/                     # Shared module
│   ├── shared/
│   │   ├── examples.py
│   │   ├── models.py               # Pydantic models
│   │   └── sample_data.py
│   └── models.py
├── nginx/                      # Nginx configuration
├── docker-compose.yml          # Docker orchestration
└── Makefile                    # Development shortcuts
```

## New Functionality: Optimizing Cache Key Generation for Large Texts

### Current Implementation Gap

The cache key generation uses inefficient JSON serialization and MD5 hashing:

```python
def _generate_cache_key(self, text: str, operation: str, options: Dict[str, Any], question: str = None) -> str:
    cache_data = {
        "text": text,  # Large texts cause performance issues
        "operation": operation,
        "options": sorted(options.items()) if options else [],
        "question": question
    }
    content = json.dumps(cache_data, sort_keys=True)  # Expensive for large texts
    return f"ai_cache:{hashlib.md5(content.encode()).hexdigest()}"  # MD5 on large strings
```

**Critical Issues:**
- **Quadratic Complexity**: JSON serialization of large text becomes expensive
- **Memory Overhead**: Full text is serialized into JSON before hashing
- **CPU Intensive**: MD5 hashing large JSON strings
- **No Text Size Optimization**: No consideration for text length in caching strategy

### Improvement Opportunities

#### 1. **Text Hashing Strategy**

```python
import hashlib
from typing import Optional, Dict, Any

class CacheKeyGenerator:
    def __init__(self):
        self.text_hash_threshold = 1000  # Characters
        self.hash_algorithm = hashlib.sha256  # More secure than MD5
    
    def _hash_text_efficiently(self, text: str) -> str:
        """Efficiently hash text using streaming approach."""
        if len(text) <= self.text_hash_threshold:
            # For short texts, use text directly
            return text
        
        # For large texts, hash in chunks to reduce memory usage
        hasher = self.hash_algorithm()
        
        # Add text content
        hasher.update(text.encode('utf-8'))
        
        # Add text metadata for uniqueness
        hasher.update(f"len:{len(text)}".encode('utf-8'))
        hasher.update(f"words:{len(text.split())}".encode('utf-8'))
        
        return f"hash:{hasher.hexdigest()[:16]}"  # Shorter hash for efficiency
    
    def generate_cache_key(
        self, 
        text: str, 
        operation: str, 
        options: Dict[str, Any], 
        question: Optional[str] = None
    ) -> str:
        """Generate optimized cache key with efficient text handling."""
        
        # Hash text efficiently
        text_identifier = self._hash_text_efficiently(text)
        
        # Create lightweight cache components
        cache_components = [
            f"op:{operation}",
            f"txt:{text_identifier}"
        ]
        
        # Add options efficiently
        if options:
            # Sort and format options more efficiently
            opts_str = "&".join(f"{k}={v}" for k, v in sorted(options.items()))
            cache_components.append(f"opts:{hashlib.md5(opts_str.encode()).hexdigest()[:8]}")
        
        # Add question if present
        if question:
            q_hash = hashlib.md5(question.encode()).hexdigest()[:8]
            cache_components.append(f"q:{q_hash}")
        
        # Combine components efficiently
        cache_key = "ai_cache:" + "|".join(cache_components)
        
        return cache_key
```

#### 2. **Tiered Caching Strategy**

```python
class AIResponseCache:
    def __init__(self):
        # ... existing code ...
        self.text_size_tiers = {
            'small': 500,      # < 500 chars - cache with full text
            'medium': 5000,    # 500-5000 chars - cache with text hash
            'large': 50000,    # 5000-50000 chars - cache with content hash + metadata
        }
        self.memory_cache = {}  # In-memory cache for frequently accessed small items
        self.memory_cache_size = 100
    
    def _get_text_tier(self, text: str) -> str:
        """Determine caching tier based on text size."""
        text_len = len(text)
        if text_len < self.text_size_tiers['small']:
            return 'small'
        elif text_len < self.text_size_tiers['medium']:
            return 'medium'
        elif text_len < self.text_size_tiers['large']:
            return 'large'
        else:
            return 'xlarge'
    
    async def get_cached_response(
        self, 
        text: str, 
        operation: str, 
        options: Dict[str, Any], 
        question: str = None
    ) -> Optional[Dict[str, Any]]:
        """Multi-tier cache retrieval."""
        
        tier = self._get_text_tier(text)
        cache_key = self.key_generator.generate_cache_key(text, operation, options, question)
        
        # Check memory cache first for small items
        if tier == 'small' and cache_key in self.memory_cache:
            logger.debug(f"Memory cache hit for {operation}")
            return self.memory_cache[cache_key]
        
        # Check Redis cache
        if not await self.connect():
            return None
        
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                result = json.loads(cached_data)
                
                # Populate memory cache for small items
                if tier == 'small':
                    self._update_memory_cache(cache_key, result)
                
                logger.debug(f"Redis cache hit for {operation} (tier: {tier})")
                return result
                
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        
        return None
    
    def _update_memory_cache(self, key: str, value: Dict[str, Any]):
        """Update memory cache with LRU eviction."""
        if len(self.memory_cache) >= self.memory_cache_size:
            # Remove oldest item (simple FIFO, could implement true LRU)
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = value
```

#### 3. **Compressed Caching for Large Texts**

```python
import zlib
import pickle
from typing import Any

class AIResponseCache:
    def __init__(self):
        # ... existing code ...
        self.compression_threshold = 1000  # Bytes
        self.compression_level = 6  # Balance between speed and compression
    
    def _compress_data(self, data: Dict[str, Any]) -> bytes:
        """Compress cache data for large responses."""
        # Use pickle for Python objects, then compress
        pickled_data = pickle.dumps(data)
        
        if len(pickled_data) > self.compression_threshold:
            compressed = zlib.compress(pickled_data, self.compression_level)
            logger.debug(f"Compressed cache data: {len(pickled_data)} -> {len(compressed)} bytes")
            return b"compressed:" + compressed
        
        return b"raw:" + pickled_data
    
    def _decompress_data(self, data: bytes) -> Dict[str, Any]:
        """Decompress cache data."""
        if data.startswith(b"compressed:"):
            compressed_data = data[11:]  # Remove "compressed:" prefix
            pickled_data = zlib.decompress(compressed_data)
        else:
            pickled_data = data[4:]  # Remove "raw:" prefix
        
        return pickle.loads(pickled_data)
    
    async def cache_response(
        self, 
        text: str, 
        operation: str, 
        options: Dict[str, Any], 
        response: Dict[str, Any], 
        question: str = None
    ):
        """Cache response with compression for large data."""
        if not await self.connect():
            return
        
        cache_key = self.key_generator.generate_cache_key(text, operation, options, question)
        ttl = self.operation_ttls.get(operation, self.default_ttl)
        
        try:
            # Add cache metadata
            cached_response = {
                **response,
                "cached_at": datetime.now().isoformat(),
                "cache_hit": True,
                "text_length": len(text),
                "compression_used": len(str(response)) > self.compression_threshold
            }
            
            # Compress if beneficial
            cache_data = self._compress_data(cached_response)
            
            await self.redis.setex(cache_key, ttl, cache_data)
            
            logger.debug(f"Cached response for {operation} (size: {len(cache_data)} bytes)")
            
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")
```

#### 4. **Performance Monitoring**

```python
class CachePerformanceMonitor:
    def __init__(self):
        self.key_generation_times = []
        self.cache_operation_times = []
        self.compression_ratios = []
    
    def record_key_generation_time(self, duration: float, text_length: int):
        """Record key generation performance."""
        self.key_generation_times.append({
            'duration': duration,
            'text_length': text_length,
            'timestamp': time.time()
        })
        
        # Keep only recent measurements
        cutoff = time.time() - 3600  # Last hour
        self.key_generation_times = [
            t for t in self.key_generation_times 
            if t['timestamp'] > cutoff
        ]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        if not self.key_generation_times:
            return {}
        
        durations = [t['duration'] for t in self.key_generation_times]
        text_lengths = [t['text_length'] for t in self.key_generation_times]
        
        return {
            'avg_key_generation_time': sum(durations) / len(durations),
            'max_key_generation_time': max(durations),
            'avg_text_length': sum(text_lengths) / len(text_lengths),
            'total_operations': len(durations)
        }
```
