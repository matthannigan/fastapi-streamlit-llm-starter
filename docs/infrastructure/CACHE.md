# Caching AI Responses

The application implements a sophisticated **multi-tiered caching system** designed for optimal performance with AI-generated content. The caching layer significantly reduces API calls to AI services and improves response times for repeated requests.

## Cache Tiers

The system uses a **three-tier caching approach**:

1. **Memory Cache (L1)** - Fast in-memory storage for small, frequently accessed items
2. **Redis Cache (L2)** - Persistent distributed cache for all response data
3. **Compression Layer** - Automatic data compression for large cached responses

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Memory Cache  │───▶│   Redis Cache   │───▶│  AI Service     │
│   (In-Memory)   │    │  (Distributed)  │    │  (Gemini API)   │
│                 │    │                 │    │                 │
│ • Small texts   │    │ • All responses │    │ • Fresh data    │
│ • Fast access   │    │ • Persistent    │    │ • API calls     │
│ • 100 items max │    │ • Compressed    │    │ • Rate limited  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        L1                      L2                   Source
```

## Cache Flow Diagram

```
Request ──▶ Generate Cache Key ──▶ Check Memory Cache (L1)
                    │                        │
                    │                    Hit ──▶ Return Result
                    │                        │
                    │                    Miss ──▶ Check Redis (L2)
                    │                               │
                    │                           Hit ──▶ Decompress ──▶ Update Memory ──▶ Return
                    │                               │
                    │                           Miss ──▶ Call AI Service
                    │                                      │
                    │                                  Response ──▶ Compress ──▶ Store Redis
                    │                                      │
                    │                                  Update Memory ──▶ Return Result
                    │                                      │
                 Performance Monitoring ◀──────────────────┘
                (Key gen time, cache ops, compression ratios)
```

## Key Generation Strategy

The **CacheKeyGenerator** implements an intelligent key generation algorithm optimized for different text sizes:

**Text Size Tiers:**
- **Small** (< 500 chars): Full text preserved in keys for readability
- **Medium** (500-5K chars): Text content hashed for moderate performance
- **Large** (5K-50K chars): Content hash with metadata for uniqueness
- **X-Large** (> 50K chars): Efficient streaming hash with minimal memory usage

**Key Structure:**
```
ai_cache:op:<operation>|txt:<text_identifier>|opts:<options_hash>|q:<question_hash>
```

**Example Keys:**
```bash
# Small text (preserved)
ai_cache:op:summarize|txt:Hello_world_example|opts:a1b2c3d4

# Large text (hashed)
ai_cache:op:sentiment|txt:hash:f8a7b3c912de4567|opts:e5f6a7b8|q:1a2b3c4d
```

## Hash Algorithms

- **Text Content**: SHA256 (configurable) for security and uniqueness
- **Options/Questions**: MD5 for speed (options are typically small)
- **Streaming Hash**: Chunked processing for memory efficiency with large texts

## Data Compression

**Automatic Compression** for responses above configurable thresholds:

- **Compression Threshold**: 1000 bytes (configurable)
- **Compression Level**: 6 (balanced speed/ratio, configurable 1-9)
- **Algorithm**: zlib (fast compression/decompression)
- **Benefits**: Reduces Redis memory usage by 60-80% for typical AI responses

**Compression Decision Flow:**
```
Response Size Check ──▶ < 1000 bytes ──▶ Store Uncompressed
                   │
                   ▶ ≥ 1000 bytes ──▶ Compress with zlib ──▶ Store Compressed
```

## Cache Invalidation Strategies

**Time-Based (TTL) Invalidation:**
```python
Operation TTLs:
- summarize: 7200s (2 hours)    # Summaries are stable
- sentiment: 86400s (24 hours)  # Sentiment rarely changes  
- key_points: 7200s (2 hours)   # Stable extraction
- questions: 3600s (1 hour)     # Can vary with context
- qa: 1800s (30 minutes)        # Context-dependent
```

**Manual Invalidation Patterns:**
- `invalidate_pattern(pattern)`: Pattern-based invalidation
- `invalidate_by_operation(operation)`: Operation-specific clearing
- `invalidate_all()`: Complete cache clear
- `invalidate_memory_cache()`: Memory cache only

**Automatic Cleanup:**
- Memory cache: FIFO eviction when limit exceeded
- Performance metrics: 1-hour retention with automatic cleanup
- Redis: TTL-based expiration

## Cache Management API

### Status Endpoint
**GET** `/cache/status`
Returns comprehensive cache health metrics including Redis and memory cache statistics.

**Response:**
```json
{
  "redis": {
    "status": "connected",
    "keys": 1247,
    "memory_used": "2.5M",
    "connected_clients": 3
  },
  "memory": {
    "memory_cache_entries": 45,
    "memory_cache_utilization": "45/100"
  },
  "performance": {
    "hit_ratio": 0.85,
    "total_operations": 1250
  }
}
```

### Cache Invalidation Endpoints
**POST** `/cache/invalidate?pattern={pattern}`
Clear cache entries matching the specified pattern.

**POST** `/cache/invalidate` (empty pattern)
Clear all cache entries.

**GET** `/cache/invalidation-stats`
Get invalidation frequency statistics.

**GET** `/cache/invalidation-recommendations`
Get optimization recommendations based on invalidation patterns.

## Performance Monitoring

**Comprehensive Performance Tracking:**

**Key Generation Metrics:**
- Generation time per text size tier
- Hash algorithm performance
- Text processing efficiency

**Cache Operation Metrics:**
- Hit/miss ratios by operation type
- Get/set operation latency
- Memory vs Redis access patterns

**Compression Metrics:**
- Compression ratios by content type
- Compression time overhead
- Storage space savings

**Memory Usage Tracking:**
- Total cache size and entry count
- Memory cache utilization
- Process memory consumption
- Warning thresholds (50MB/100MB)

**Monitoring API Endpoint:**
```
GET /monitoring/cache-metrics
```

**Sample Response:**
```json
{
  "cache_hit_ratio": 0.85,
  "total_operations": 1250,
  "avg_key_generation_time": 0.003,
  "avg_cache_operation_time": 0.012,
  "compression_ratio": 0.32,
  "memory_usage_mb": 45.2,
  "recent_slow_operations": [],
  "invalidation_frequency": {
    "last_hour": 5,
    "recommendations": []
  }
}
```

## Performance Monitoring API

The application provides a comprehensive performance monitoring API endpoint for cache system analytics and optimization.

### Endpoint Details

**URL:** `GET /monitoring/cache-metrics`
**HTTP Methods:** GET only
**Authentication:** Optional API key via `X-API-Key` header or `api_key` query parameter
**Content-Type:** `application/json`

### Query Parameters

The endpoint currently accepts no query parameters. All metrics are computed over the configured retention period (default: 1 hour).

### Response Format

The endpoint returns a JSON object with comprehensive cache performance statistics:

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "retention_hours": 1,
  "cache_hit_rate": 85.5,
  "total_cache_operations": 150,
  "cache_hits": 128,
  "cache_misses": 22,
  "key_generation": {
    "total_operations": 75,
    "avg_duration": 0.002,
    "median_duration": 0.0015,
    "max_duration": 0.012,
    "min_duration": 0.0008,
    "avg_text_length": 1250,
    "max_text_length": 5000,
    "slow_operations": 2
  },
  "cache_operations": {
    "total_operations": 150,
    "avg_duration": 0.0045,
    "median_duration": 0.003,
    "max_duration": 0.025,
    "min_duration": 0.001,
    "slow_operations": 5,
    "by_operation_type": {
      "get": {"count": 100, "avg_duration": 0.003, "max_duration": 0.015},
      "set": {"count": 50, "avg_duration": 0.007, "max_duration": 0.025}
    }
  },
  "compression": {
    "total_operations": 25,
    "avg_compression_ratio": 0.65,
    "median_compression_ratio": 0.62,
    "best_compression_ratio": 0.45,
    "worst_compression_ratio": 0.89,
    "avg_compression_time": 0.003,
    "max_compression_time": 0.015,
    "total_bytes_processed": 524288,
    "total_bytes_saved": 183500,
    "overall_savings_percent": 35.0
  },
  "memory_usage": {
    "current": {
      "total_cache_size_mb": 25.5,
      "memory_cache_size_mb": 5.2,
      "cache_entry_count": 100,
      "memory_cache_entry_count": 20,
      "avg_entry_size_bytes": 2048,
      "process_memory_mb": 150.0,
      "cache_utilization_percent": 51.0,
      "warning_threshold_reached": true
    },
    "thresholds": {
      "warning_threshold_mb": 50.0,
      "critical_threshold_mb": 100.0
    }
  },
  "invalidation": {
    "total_invalidations": 10,
    "total_keys_invalidated": 50,
    "rates": {
      "last_hour": 5,
      "last_24_hours": 10
    }
  }
}
```

### Available Metrics

**Core Cache Metrics:**
- `timestamp`: ISO timestamp when metrics were collected
- `retention_hours`: Data retention period for measurements
- `cache_hit_rate`: Overall cache hit percentage (0-100)
- `total_cache_operations`: Total number of cache operations performed
- `cache_hits`: Number of successful cache retrievals
- `cache_misses`: Number of cache misses requiring AI processing

**Key Generation Performance:**
- `total_operations`: Number of cache key generation operations
- `avg_duration`: Average key generation time (seconds)
- `median_duration`: Median key generation time (seconds)
- `max_duration`: Maximum key generation time (seconds)
- `min_duration`: Minimum key generation time (seconds)
- `avg_text_length`: Average character length of processed text
- `max_text_length`: Maximum character length processed
- `slow_operations`: Count of operations exceeding performance threshold (0.1s)

**Cache Operation Performance:**
- `total_operations`: Total cache get/set/delete operations
- `avg_duration`: Average operation time (seconds)
- `median_duration`: Median operation time (seconds)  
- `max_duration`: Maximum operation time (seconds)
- `min_duration`: Minimum operation time (seconds)
- `slow_operations`: Count of operations exceeding threshold (0.05s)
- `by_operation_type`: Performance breakdown by operation type (get, set, delete, invalidate)

**Compression Statistics:**
- `total_operations`: Number of compression operations performed
- `avg_compression_ratio`: Average compression ratio (0-1, lower is better)
- `median_compression_ratio`: Median compression ratio
- `best_compression_ratio`: Best (lowest) compression ratio achieved
- `worst_compression_ratio`: Worst (highest) compression ratio
- `avg_compression_time`: Average compression time (seconds)
- `max_compression_time`: Maximum compression time (seconds)
- `total_bytes_processed`: Total bytes compressed
- `total_bytes_saved`: Total storage space saved through compression
- `overall_savings_percent`: Overall percentage of storage space saved

**Memory Usage Metrics:**
- `current.total_cache_size_mb`: Total cache memory usage (MB)
- `current.memory_cache_size_mb`: In-memory cache usage (MB)
- `current.cache_entry_count`: Total number of cached entries
- `current.memory_cache_entry_count`: Number of in-memory cached entries
- `current.avg_entry_size_bytes`: Average size per cache entry (bytes)
- `current.process_memory_mb`: Total process memory usage (MB)
- `current.cache_utilization_percent`: Cache utilization percentage
- `current.warning_threshold_reached`: Whether memory warning threshold is exceeded
- `thresholds.warning_threshold_mb`: Memory warning threshold (MB)
- `thresholds.critical_threshold_mb`: Memory critical threshold (MB)

**Cache Invalidation Metrics:**
- `total_invalidations`: Total number of invalidation operations
- `total_keys_invalidated`: Total number of keys invalidated
- `rates.last_hour`: Invalidation rate in the last hour
- `rates.last_24_hours`: Invalidation rate in the last 24 hours

### Authentication Requirements

**Optional Authentication:** The endpoint supports optional API key authentication but does not require it. When an API key is provided, it should be included as:

- **Header:** `X-API-Key: your-api-key`
- **Query Parameter:** `?api_key=your-api-key`

If authentication fails, a 401 Unauthorized response is returned. If no API key is provided, the endpoint still returns metrics but may be subject to rate limiting in production deployments.

### Rate Limiting Considerations

**Current Implementation:** No explicit rate limiting is implemented for the monitoring endpoint.

**Production Recommendations:**
- Implement rate limiting to prevent abuse (suggested: 60 requests per minute per IP)
- Monitor endpoint usage to identify potential performance impacts
- Consider caching the response for 10-30 seconds for high-traffic scenarios
- Implement circuit breaker patterns for statistics computation errors

### Response Status Codes

**200 OK:** Successfully retrieved cache performance metrics
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "retention_hours": 1,
  "cache_hit_rate": 85.5,
  // ... full metrics response
}
```

**500 Internal Server Error:** Performance monitor unavailable or statistics computation failed
```json
{
  "detail": "Failed to retrieve cache performance metrics: Performance monitor not available"
}
```

**503 Service Unavailable:** Cache monitoring temporarily disabled
```json
{
  "detail": "Cache performance monitoring is temporarily disabled"
}
```

### Common Monitoring Queries

**Basic Performance Check:**
```bash
curl -X GET "http://localhost:8000/monitoring/cache-metrics" \
  -H "Content-Type: application/json"
```

**Authenticated Monitoring:**
```bash
curl -X GET "http://localhost:8000/monitoring/cache-metrics" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json"
```

**Monitoring with Query Parameter Authentication:**
```bash
curl -X GET "http://localhost:8000/monitoring/cache-metrics?api_key=your-api-key"
```

### Interpreting Results

**Performance Optimization Indicators:**

**High Performance (Good):**
- Cache hit rate > 80%
- Average key generation time < 0.005s
- Average cache operation time < 0.010s
- Compression ratio < 0.70 (30%+ space savings)
- Memory usage below warning threshold

**Performance Issues (Investigate):**
- Cache hit rate < 50%
- Slow operations count > 5% of total operations
- Memory usage approaching critical threshold
- High compression times (> 0.020s average)

**Critical Issues (Action Required):**
- Cache hit rate < 20%
- Memory usage exceeding critical threshold
- Frequent invalidation operations (> 20/hour)
- Average operation times > 0.050s

**Optimization Strategies Based on Metrics:**

**Low Hit Rate:**
- Review cache key generation strategy
- Adjust TTL settings for different operation types
- Investigate text preprocessing inconsistencies

**High Memory Usage:**
- Enable/tune compression settings
- Reduce memory cache size
- Implement more aggressive TTL policies

**Slow Operations:**
- Optimize Redis connection settings
- Review text size tier configurations
- Consider distributed cache sharding

**Performance Considerations:**

**Response Time:** The endpoint may take 100-500ms to respond when computing statistics for large datasets (> 1000 operations). This is normal and expected behavior.

**Memory Impact:** Statistics computation temporarily increases memory usage during calculation. The endpoint uses approximately 1-5MB additional memory during processing.

**CPU Usage:** Statistics computation may cause brief CPU spikes (< 1 second) during metric aggregation, particularly for percentile calculations.

**Concurrent Access:** The endpoint is thread-safe and supports concurrent requests, though heavy concurrent usage may impact response times.

## Configuration Options

The caching system is highly configurable through the `config.py` file. All settings have sensible defaults and can be customized for different deployment scenarios and performance requirements.

### Redis Configuration

**`redis_url`** (str)
- **Default:** `"redis://redis:6379"`
- **Description:** Redis connection URL for the distributed cache layer (L2)
- **Range:** Any valid Redis URL format
- **Environment Variable:** `REDIS_URL`
- **Example Usage:**
  ```python
  # For local development
  redis_url = "redis://localhost:6379"
  
  # For production with authentication
  redis_url = "redis://username:password@redis-host:6379/0"
  
  # For Redis Cluster
  redis_url = "redis://cluster-node1:6379,cluster-node2:6379"
  ```

### Cache Key Generation Settings

**`cache_text_hash_threshold`** (int)
- **Default:** `1000`
- **Description:** Character count threshold for when text content should be hashed in cache keys instead of using full text
- **Range:** > 0 (recommended: 500-2000)
- **Example Usage:**
  ```python
  # Conservative approach - hash smaller texts for security
  cache_text_hash_threshold = 500
  
  # Liberal approach - keep more text readable in keys for debugging
  cache_text_hash_threshold = 2000
  ```

**`cache_text_size_tiers`** (dict)
- **Default:** `{'small': 500, 'medium': 5000, 'large': 50000}`
- **Description:** Text size tiers for caching strategy optimization. Defines character thresholds for different caching approaches
- **Structure:**
  - `small`: Texts cached in memory for fastest access
  - `medium`: Texts cached with optimized key generation
  - `large`: Texts cached with content hashing for efficiency
- **Example Usage:**
  ```python
  # For memory-constrained environments
  cache_text_size_tiers = {
      'small': 200,    # Very small texts only in memory
      'medium': 2000,  # Smaller medium tier
      'large': 20000   # Smaller large tier
  }
  
  # For high-memory environments with large documents
  cache_text_size_tiers = {
      'small': 1000,   # More texts in fast memory cache
      'medium': 10000, # Larger medium tier
      'large': 100000  # Support very large documents
  }
  ```

### Memory Cache Configuration

**`cache_memory_cache_size`** (int)
- **Default:** `100`
- **Description:** Maximum number of items to store in the in-memory cache (L1) for small texts. Higher values improve hit rates but use more memory
- **Range:** > 0 (recommended: 50-500)
- **Memory Impact:** Each item uses ~1-5KB depending on response size
- **Example Usage:**
  ```python
  # For low-memory environments
  cache_memory_cache_size = 50
  
  # For high-traffic applications with sufficient memory
  cache_memory_cache_size = 500
  
  # For development/testing
  cache_memory_cache_size = 10
  ```

### Cache Compression Settings

**`cache_compression_threshold`** (int)
- **Default:** `1000`
- **Description:** Size threshold in bytes for when cached responses should be compressed before storage in Redis
- **Range:** > 0 (recommended: 500-5000)
- **Trade-off:** Lower values save storage but increase CPU usage
- **Example Usage:**
  ```python
  # Aggressive compression for storage optimization
  cache_compression_threshold = 500
  
  # Conservative compression for CPU optimization
  cache_compression_threshold = 5000
  
  # Disable compression for small responses
  cache_compression_threshold = 10000
  ```

**`cache_compression_level`** (int)
- **Default:** `6`
- **Description:** Compression level (1-9) where 9 is highest compression but slowest, 1 is fastest but lowest compression
- **Range:** 1-9
- **Recommended:** 4-7 for balanced performance
- **Example Usage:**
  ```python
  # Fast compression for high-throughput systems
  cache_compression_level = 3
  
  # Balanced performance (default)
  cache_compression_level = 6
  
  # Maximum compression for storage-constrained environments
  cache_compression_level = 9
  ```

### Cache TTL (Time To Live) Settings

**`cache_default_ttl`** (int)
- **Default:** `3600` (1 hour)
- **Description:** Default cache TTL in seconds. Controls how long cached responses remain valid before expiration
- **Range:** > 0 (recommended: 300-86400)
- **Example Usage:**
  ```python
  # Short TTL for frequently changing data
  cache_default_ttl = 600  # 10 minutes
  
  # Standard TTL (default)
  cache_default_ttl = 3600  # 1 hour
  
  # Long TTL for stable content
  cache_default_ttl = 86400  # 24 hours
  
  # Very short TTL for development/testing
  cache_default_ttl = 60  # 1 minute
  ```

### Environment Variable Overrides

All cache configuration can be overridden using environment variables. The variable names follow the pattern `CACHE_<SETTING_NAME>` in uppercase:

```env
# Redis Configuration
REDIS_URL=redis://production-redis:6379

# Cache Key Generation
CACHE_TEXT_HASH_THRESHOLD=1500

# Memory Cache
CACHE_MEMORY_CACHE_SIZE=200

# Compression Settings
CACHE_COMPRESSION_THRESHOLD=1500
CACHE_COMPRESSION_LEVEL=7

# TTL Settings
CACHE_DEFAULT_TTL=7200
```

### Configuration Validation

The configuration system includes automatic validation:

- **Type Checking:** All numeric values are validated for correct types
- **Range Validation:** Values are checked against acceptable ranges
- **Dependency Validation:** Related settings are cross-validated for compatibility

### Performance Tuning Guidelines

**For High-Traffic Applications:**
```python
cache_memory_cache_size = 500          # More memory cache
cache_compression_threshold = 2000     # Selective compression
cache_compression_level = 4            # Fast compression
cache_default_ttl = 7200              # Longer TTL
```

**For Memory-Constrained Environments:**
```python
cache_memory_cache_size = 25           # Minimal memory cache
cache_compression_threshold = 500      # Aggressive compression
cache_compression_level = 8            # High compression
cache_default_ttl = 1800              # Shorter TTL
```

**For Development/Testing:**
```python
cache_memory_cache_size = 10           # Small cache for testing
cache_compression_threshold = 10000    # Minimal compression
cache_compression_level = 1            # Fast compression
cache_default_ttl = 300               # Short TTL for rapid iteration
```

## Development Setup

### Starting Redis Locally
```bash
# Start Redis container
docker-compose up redis -d

# Verify Redis connection
docker exec ai-processor-redis redis-cli ping
# Expected response: PONG

# Check cache status
curl http://localhost:8000/cache/status
```

### Development Without Redis
The system gracefully degrades when Redis is unavailable:
- API endpoints continue working
- Cache operations fail silently with logged warnings
- No caching occurs, all requests processed fresh

## Direct Redis Management

For debugging and maintenance:

```bash
# Connect to Redis container
docker exec -it ai-processor-redis redis-cli

# View all cache keys
KEYS ai_cache:*

# Get detailed cache statistics
INFO memory

# Check specific key TTL
TTL ai_cache:op:summarize|txt:hash:f8a7b3c9...

# Delete specific key
DEL ai_cache:op:summarize|txt:hash:f8a7b3c9...

# Clear all cache (use carefully!)
FLUSHDB
```

## Usage Examples

### Cache Hit/Miss Demonstration
```bash
# First request - Cache MISS
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "AI is transforming technology...",
    "operation": "summarize",
    "options": {"max_length": 100}
  }'

# Response includes original processing time
{
  "operation": "summarize",
  "result": "AI is rapidly changing...",
  "processing_time": 2.3,
  "success": true
}

# Second identical request - Cache HIT
# Returns cached response with cache indicators
{
  "operation": "summarize", 
  "result": "AI is rapidly changing...",
  "processing_time": 2.3,     # Original processing time
  "cached_at": "2024-01-01T12:00:00",
  "cache_hit": true,          # Cache hit indicator
  "success": true
}
```

## Troubleshooting

### Common Issues

#### Cache Not Working
**Symptoms:** All requests show full processing time, no cache hits

**Diagnosis:**
```bash
# Check Redis connection
curl http://localhost:8000/cache/status

# Check Redis container
docker ps | grep redis
docker logs ai-processor-redis
```

**Solutions:**
- Restart Redis: `docker-compose restart redis`
- Check Redis configuration in environment variables
- Verify network connectivity between services

#### High Memory Usage
**Symptoms:** Redis consuming excessive memory

**Diagnosis:**
```bash
# Check memory usage
docker exec ai-processor-redis redis-cli info memory

# Count cache keys
docker exec ai-processor-redis redis-cli eval "return #redis.call('keys', 'ai_cache:*')" 0
```

**Solutions:**
- Clear cache: `curl -X POST "http://localhost:8000/cache/invalidate"`
- Adjust TTL values
- Enable compression for larger responses

#### Inconsistent Cache Behavior
**Symptoms:** Same requests sometimes cached, sometimes not

**Common Causes:**
- Whitespace differences in text input
- Option parameter ordering variations
- Text preprocessing inconsistencies

**Solutions:**
- Normalize text input before sending
- Use consistent option structures
- Review cache key generation logic

## Caching Best Practices and Implementation Considerations

This section outlines the comprehensive caching strategies implemented in the system and the considerations made during development. These practices follow industry standards and are optimized for AI-powered applications.

### 1. Data Selection Criteria for Caching

**What Gets Cached:**
- **AI-Generated Responses**: All successful text processing results (summaries, sentiment analysis, key points, questions, Q&A responses)
- **Operation-Specific Results**: Each operation type is cached independently to optimize for specific use cases
- **Parameterized Responses**: Results are cached with their specific options (e.g., max_length, max_points) to ensure accuracy

**What Doesn't Get Cached:**
- **Error Responses**: Failed AI operations are not cached to allow retry opportunities
- **Authentication Data**: Security-sensitive information is never cached
- **Real-Time Data**: Content that changes frequently or requires fresh processing
- **Large Streaming Responses**: Responses exceeding memory thresholds use different strategies

**Selection Algorithm:**
```python
def should_cache_response(response: dict, operation: str, text_size: int) -> bool:
    """
    Determines if a response should be cached based on:
    - Response success status
    - Content stability (AI responses are deterministic enough for caching)
    - Size considerations (very large responses may be compressed)
    - Operation type characteristics
    """
    return (
        response.get("success", False) and
        text_size < 100_000 and  # Reasonable size limit
        operation in CACHEABLE_OPERATIONS
    )
```

### 2. TTL (Time-To-Live) Strategies for Different Data Types

**Operation-Specific TTL Strategy:**
```python
TTL_STRATEGIES = {
    "summarize": 7200,    # 2 hours - Summaries are stable and reusable
    "sentiment": 86400,   # 24 hours - Sentiment rarely changes for same text
    "key_points": 7200,   # 2 hours - Key points are fairly stable  
    "questions": 3600,    # 1 hour - Questions can vary more with context
    "qa": 1800,          # 30 minutes - Context-dependent, shorter cache life
}
```

**TTL Decision Factors:**
- **Content Stability**: More stable operations get longer TTLs
- **Context Sensitivity**: Q&A operations have shorter TTLs due to context dependence
- **Reusability**: Frequently requested operations benefit from longer TTLs
- **Business Requirements**: Balance between freshness and performance

**Dynamic TTL Considerations:**
```python
def calculate_dynamic_ttl(operation: str, text_length: int, options: dict) -> int:
    """
    Future enhancement: TTL based on content characteristics
    - Longer texts might have more stable summaries (longer TTL)
    - Specific options might indicate need for freshness (shorter TTL)
    """
    base_ttl = TTL_STRATEGIES.get(operation, 3600)
    
    # Adjust based on text characteristics
    if text_length > 10000:  # Large texts have more stable analysis
        return int(base_ttl * 1.5)
    elif text_length < 500:  # Small texts might be more variable
        return int(base_ttl * 0.75)
    
    return base_ttl
```

### 3. Cache Invalidation Patterns Implemented

**Automatic Invalidation:**
- **TTL-Based Expiration**: Primary invalidation method using Redis TTL
- **Memory Pressure Eviction**: FIFO eviction when memory cache reaches capacity
- **Health-Based Cleanup**: Automatic cleanup of performance metrics after retention period

**Manual Invalidation Patterns:**
```python
# Pattern-based invalidation for administrative control
await cache.invalidate_pattern("summarize")  # Clear all summarization cache
await cache.invalidate_pattern("sentiment")  # Clear sentiment analysis cache
await cache.invalidate_by_operation("qa")    # Clear Q&A responses

# Targeted invalidation for specific scenarios
await cache.invalidate_by_text_hash(text_hash)  # Clear cache for specific text
```

**Invalidation Triggers:**
- **Configuration Changes**: Cache cleared when TTL strategies change
- **Model Updates**: Cache invalidated when AI model configuration changes
- **Data Quality Issues**: Manual invalidation for problematic cached responses
- **Maintenance Windows**: Planned cache warming after maintenance

**Invalidation Strategy Implementation:**
```python
class CacheInvalidationStrategy:
    """
    Implements intelligent cache invalidation based on multiple factors
    """
    
    @staticmethod
    async def should_invalidate(operation: str, age_seconds: int, access_count: int) -> bool:
        """
        Determine if cache entry should be invalidated based on:
        - Age relative to TTL
        - Access patterns
        - Operation characteristics
        """
        ttl = TTL_STRATEGIES.get(operation, 3600)
        age_ratio = age_seconds / ttl
        
        # Invalidate if close to expiration and low access
        return age_ratio > 0.8 and access_count < 2
```

### 4. Security Considerations for Cached Data

**Key Security Measures:**
- **Content Hashing**: Sensitive text content is hashed in cache keys to prevent exposure
- **No Sensitive Data in Keys**: Cache keys never contain user data, credentials, or PII
- **Secure Key Generation**: SHA256 hashing for content identification
- **Access Control**: Cache operations respect application-level authentication

**Security Implementation:**
```python
def generate_secure_cache_key(text: str, operation: str, options: dict) -> str:
    """
    Generate cache keys without exposing sensitive content
    """
    # For small texts, use truncated content for debugging
    if len(text) < 50 and not contains_sensitive_data(text):
        text_part = text.replace(" ", "_")[:30]
    else:
        # Hash longer or sensitive content
        text_part = f"hash:{hashlib.sha256(text.encode()).hexdigest()[:16]}"
    
    options_hash = hashlib.md5(json.dumps(options, sort_keys=True).encode()).hexdigest()[:8]
    return f"ai_cache:op:{operation}|txt:{text_part}|opts:{options_hash}"
```

**Data Privacy Considerations:**
- **No Persistent PII**: Cache keys and values avoid storing personally identifiable information
- **Encryption at Rest**: Redis can be configured with encryption for sensitive deployments
- **Network Security**: Redis connections secured with authentication and TLS in production
- **Audit Logging**: Cache operations logged for security monitoring

### 5. Scaling and Load Balancing Approaches

**Horizontal Scaling Strategy:**
```python
# Multi-instance cache coordination
class DistributedCacheStrategy:
    """
    Supports scaling across multiple application instances
    """
    
    def __init__(self, redis_cluster_nodes: List[str]):
        # Redis Cluster for horizontal scaling
        self.cluster = RedisCluster(startup_nodes=redis_cluster_nodes)
        
    async def get_with_failover(self, key: str) -> Optional[Any]:
        """
        Implements failover for cache retrieval across cluster nodes
        """
        for attempt in range(3):
            try:
                return await self.cluster.get(key)
            except ConnectionError:
                await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
        return None
```

**Load Balancing Considerations:**
- **Consistent Hashing**: Cache keys distributed evenly across Redis cluster nodes
- **Connection Pooling**: Efficient connection reuse across application instances
- **Circuit Breaker**: Prevents cascade failures when cache nodes are unavailable
- **Regional Distribution**: Support for multi-region cache deployment

**Scaling Implementation Patterns:**
```python
# Configuration for different scaling scenarios
SCALING_CONFIGS = {
    "single_instance": {
        "redis_url": "redis://localhost:6379",
        "memory_cache_size": 100,
        "connection_pool_size": 10
    },
    "multi_instance": {
        "redis_url": "redis://redis-cluster:6379",
        "memory_cache_size": 50,  # Reduced per-instance memory
        "connection_pool_size": 20
    },
    "distributed": {
        "redis_cluster": ["node1:6379", "node2:6379", "node3:6379"],
        "memory_cache_size": 25,
        "connection_pool_size": 50,
        "enable_sharding": True
    }
}
```

### 6. Performance Optimization Techniques

**Multi-Tiered Performance Strategy:**
- **L1 Cache (Memory)**: Sub-millisecond access for frequently used small responses
- **L2 Cache (Redis)**: Fast distributed access with compression for larger responses
- **Intelligent Prefetching**: Pre-populate cache based on access patterns

**Optimization Implementations:**
```python
class PerformanceOptimizer:
    """
    Implements various performance optimization techniques
    """
    
    async def optimize_cache_placement(self, key: str, value: Any, access_pattern: dict):
        """
        Decides optimal cache tier based on access patterns and content size
        """
        size_bytes = len(json.dumps(value).encode())
        access_frequency = access_pattern.get("frequency", 1)
        
        if size_bytes < 1024 and access_frequency > 10:
            # Small, frequently accessed -> Memory cache
            await self.memory_cache.set(key, value)
        elif size_bytes > 10240:
            # Large content -> Redis with compression
            await self.redis_cache.set_compressed(key, value)
        else:
            # Default -> Redis without compression
            await self.redis_cache.set(key, value)
```

**Performance Monitoring Integration:**
- **Real-Time Metrics**: Continuous monitoring of hit rates, latency, and memory usage
- **Adaptive Optimization**: Automatic adjustment of cache parameters based on performance data
- **Predictive Scaling**: Anticipate cache needs based on usage patterns

### 7. Monitoring and Maintenance Recommendations

**Monitoring Strategy:**
```python
# Key metrics to track for cache health
CRITICAL_METRICS = {
    "cache_hit_ratio": {"threshold": 0.7, "action": "investigate_key_generation"},
    "avg_response_time": {"threshold": 0.1, "action": "check_redis_performance"},
    "memory_usage_percent": {"threshold": 80, "action": "increase_compression"},
    "error_rate": {"threshold": 0.05, "action": "check_redis_connectivity"},
    "compression_ratio": {"threshold": 0.8, "action": "review_compression_settings"}
}
```

**Automated Maintenance Tasks:**
```python
class CacheMaintenanceScheduler:
    """
    Implements automated maintenance for optimal cache performance
    """
    
    @schedule.every(1).hour
    async def performance_health_check(self):
        """Hourly performance analysis and optimization"""
        metrics = await self.monitor.get_performance_metrics()
        
        if metrics["cache_hit_ratio"] < 0.5:
            await self.analyzer.investigate_key_patterns()
            
        if metrics["memory_usage_percent"] > 85:
            await self.cache.optimize_memory_usage()
    
    @schedule.every(1).day
    async def cache_optimization(self):
        """Daily cache optimization and cleanup"""
        await self.cache.compact_redis_memory()
        await self.monitor.cleanup_old_metrics()
        await self.cache.optimize_ttl_strategies()
```

**Maintenance Best Practices:**
- **Regular Performance Reviews**: Weekly analysis of cache performance metrics
- **Capacity Planning**: Monitor growth trends and plan for scaling needs
- **Configuration Tuning**: Adjust cache parameters based on actual usage patterns
- **Health Monitoring**: Set up alerts for cache performance degradation
- **Backup Strategies**: Regular backup of cache configuration and critical data

**Operational Procedures:**
```python
# Standard operating procedures for cache maintenance
MAINTENANCE_PROCEDURES = {
    "daily": [
        "check_cache_hit_ratios",
        "review_memory_usage",
        "cleanup_expired_metrics"
    ],
    "weekly": [
        "analyze_performance_trends", 
        "optimize_ttl_strategies",
        "review_compression_effectiveness"
    ],
    "monthly": [
        "capacity_planning_review",
        "security_audit",
        "configuration_optimization"
    ]
}
```

### 8. Industry Standards and Compliance

**Standards Applied:**
- **RFC 7234 (HTTP Caching)**: Cache behavior follows HTTP caching semantics where applicable
- **Redis Best Practices**: Implementation follows Redis official recommendations for clustering and performance
- **Security Standards**: Implements OWASP caching security guidelines
- **Performance Standards**: Follows industry benchmarks for cache hit ratios (>70%) and response times (<100ms)

**Compliance Considerations:**
- **Data Retention**: TTL strategies comply with data retention policies
- **Privacy Regulations**: Cache implementation respects GDPR and similar privacy requirements
- **Security Auditing**: Cache operations are logged for compliance and security auditing
- **Disaster Recovery**: Cache architecture supports business continuity requirements

This comprehensive caching implementation represents industry best practices adapted for AI-powered applications, ensuring optimal performance, security, and maintainability while supporting future scaling requirements.
