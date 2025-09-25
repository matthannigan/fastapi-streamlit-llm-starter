---
sidebar_label: Troubleshooting
title: Cache Infrastructure Performance & Troubleshooting Guide
description: Comprehensive troubleshooting guide for cache infrastructure performance issues, debugging workflows, optimization strategies, and emergency procedures
---

# Cache Infrastructure Performance & Troubleshooting Guide

This guide provides systematic troubleshooting workflows, performance optimization strategies, and emergency procedures for the cache infrastructure. It consolidates debugging workflows, and resolution procedures for operational teams and developers.

## Table of Contents

1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Performance Monitoring](#performance-monitoring)
3. [Common Performance Issues](#common-performance-issues)
4. [Systematic Troubleshooting](#systematic-troubleshooting)
5. [Optimization Strategies](#optimization-strategies)
6. [Configuration Troubleshooting](#configuration-troubleshooting)
7. [Redis Connection Issues](#redis-connection-issues)
8. [Memory Management](#memory-management)
9.  [Health Check Integration](#health-check-integration)
10. [Emergency Procedures](#emergency-procedures)

## Quick Diagnostic Checklist

### Immediate Health Assessment (< 2 minutes)

**Cache System Status**:
```bash
# Test basic cache functionality
curl -f "http://localhost:8000/internal/cache/status" | jq '.'

# Check cache performance metrics
curl -s "http://localhost:8000/internal/cache/metrics" | jq '.cache_hit_rate, .total_operations'

# Verify Redis connectivity
curl -s "http://localhost:8000/internal/cache/status" | jq '.redis.status'
```

**Quick Performance Check**:
```bash
# Cache hit ratio (target: >70%)
curl -s "http://localhost:8000/internal/cache/metrics" | jq '.cache_hit_rate'

# Memory usage status
curl -s "http://localhost:8000/internal/cache/memory-stats" | jq '.total_cache_size_mb'

# Recent error indicators
curl -s "http://localhost:8000/internal/cache/health" | jq '.errors[]'
```

### Fast Resolution Commands

**Common Quick Fixes**:
```bash
# Clear problematic cache data
curl -X POST "http://localhost:8000/internal/cache/clear"

# Reset cache to safe configuration
curl -X POST "http://localhost:8000/internal/cache/reset-config"

# Force memory cleanup
curl -X POST "http://localhost:8000/internal/cache/gc"
```

**Cache Performance Reset**:
```bash
# Apply conservative settings
curl -X POST "http://localhost:8000/internal/cache/apply-preset" \
  -H "Content-Type: application/json" \
  -d '{"preset": "conservative"}'

# Restart cache service
curl -X POST "http://localhost:8000/internal/cache/restart"
```

## Performance Monitoring

### Key Performance Metrics

#### Cache Effectiveness Metrics
```bash
# Comprehensive cache statistics
curl -s "http://localhost:8000/internal/cache/metrics" | jq '{
  cache_hit_rate: .cache_hit_rate,
  total_operations: .total_operations,
  l1_hit_rate: .memory_cache_hit_rate,
  l2_hit_rate: .redis_cache_hit_rate,
  avg_response_time: .avg_operation_duration
}'
```

**Target Benchmarks**:
- **Cache Hit Rate**: >70% (excellent: >80%)
- **Memory Tier Hit Rate**: >40% for hot data
- **Average Operation Time**: Fast response for cache hits
- **Key Generation Time**: Efficient key processing

#### Memory Usage Analysis
```bash
# Memory usage breakdown
curl -s "http://localhost:8000/internal/cache/memory-stats" | jq '{
  total_memory_mb: .total_cache_size_mb,
  memory_utilization: .memory_cache_utilization,
  redis_memory_usage: .redis_memory_used,
  compression_savings: .compression_stats.total_bytes_saved
}'
```

**Warning Thresholds**:
- **Memory Usage**: 50MB warning, 100MB critical
- **Memory Utilization**: >90% utilization warning
- **Growth Rate**: >10MB/hour sustained growth

#### Compression Performance
```bash
# Compression efficiency analysis
curl -s "http://localhost:8000/internal/cache/compression-stats" | jq '{
  avg_compression_ratio: .avg_compression_ratio,
  total_savings_mb: (.total_bytes_saved / 1024 / 1024),
  compression_time_avg: .avg_compression_time,
  decompression_time_avg: .avg_decompression_time
}'
```

### Real-Time Monitoring Dashboard

```bash
# Create monitoring script for continuous tracking
cat > monitor_cache.sh << 'EOF'
#!/bin/bash

echo "=== Cache Performance Monitor ==="
date
echo

while true; do
    echo -n "$(date '+%H:%M:%S') | "
    
    # Get key metrics
    METRICS=$(curl -s "http://localhost:8000/internal/cache/metrics")
    HIT_RATE=$(echo $METRICS | jq -r '.cache_hit_rate // 0')
    OPERATIONS=$(echo $METRICS | jq -r '.total_operations // 0')
    MEMORY_MB=$(echo $METRICS | jq -r '.memory_usage.total_mb // 0')
    
    printf "Hit Rate: %5.1f%% | Operations: %6d | Memory: %5.1f MB\n" \
           $(echo "$HIT_RATE * 100" | bc) $OPERATIONS $MEMORY_MB
    
    # Check for alerts
    if (( $(echo "$HIT_RATE < 0.5" | bc -l) )); then
        echo "⚠️  WARNING: Low hit rate detected"
    fi
    
    if (( $(echo "$MEMORY_MB > 50" | bc -l) )); then
        echo "⚠️  WARNING: High memory usage detected"
    fi
    
    sleep 10
done
EOF

chmod +x monitor_cache.sh
./monitor_cache.sh
```

### Performance Analysis Tools

#### Cache Access Pattern Analysis
```bash
# Analyze cache key patterns
curl -s "http://localhost:8000/internal/cache/key-analysis" | jq '{
  total_keys: .total_keys,
  key_patterns: .patterns | to_entries | map({pattern: .key, count: .value}) | sort_by(-.count),
  avg_key_length: .avg_key_length,
  text_tier_distribution: .text_tier_stats
}'
```

#### Operation Performance Breakdown
```bash
# Performance by cache operation type
curl -s "http://localhost:8000/internal/cache/operation-stats" | jq '{
  operations: .operations | to_entries | map({
    operation: .key,
    count: .value.count,
    avg_duration: .value.avg_duration,
    hit_rate: .value.hit_rate
  }) | sort_by(-.count)
}'
```

## Common Performance Issues

### Issue 1: Low Cache Hit Rates (<50%)

#### Symptoms
- Cache hit rate consistently below 50%
- High AI service usage and costs
- Slower than expected response times
- Cache metrics show frequent misses

#### Diagnostic Workflow
```bash
# Step 1: Analyze cache key consistency
curl -s "http://localhost:8000/internal/cache/key-analysis" | jq '.key_patterns'

# Step 2: Check TTL configuration
curl -s "http://localhost:8000/internal/cache/config/current" | jq '.ttl_settings'

# Step 3: Review text preprocessing consistency
curl -s "http://localhost:8000/internal/cache/text-tier-analysis" | jq '{
  text_size_distribution: .size_distribution,
  hash_threshold_effectiveness: .hash_threshold_analysis,
  key_generation_consistency: .consistency_metrics
}'

# Step 4: Examine cache invalidation patterns
curl -s "http://localhost:8000/internal/cache/invalidation-stats" | jq '{
  invalidation_frequency: .hourly_invalidations,
  patterns_invalidated: .pattern_invalidations,
  manual_clears: .manual_clear_count
}'
```

#### Root Cause Analysis

**Key Generation Inconsistencies**:
```bash
# Test key generation with sample data
curl -X POST "http://localhost:8000/internal/cache/debug/key-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Sample text for testing",
    "operation": "summarize",
    "options": {"max_length": 100}
  }' | jq '{
    generated_key: .cache_key,
    text_length: .text_length,
    processing_method: .processing_method,
    consistency_check: .consistency_verified
  }'
```

**TTL Mismatch Issues**:
```bash
# Analyze TTL effectiveness
curl -s "http://localhost:8000/internal/cache/ttl-analysis" | jq '{
  expired_entries_rate: .expired_entries_per_hour,
  avg_entry_lifetime: .avg_lifetime_used,
  ttl_efficiency: .ttl_utilization_ratio,
  recommended_ttls: .recommendations
}'
```

#### Resolution Steps

**Fix Key Generation Consistency**:
```bash
# Reset key generation configuration
curl -X POST "http://localhost:8000/internal/cache/key-generator/reset"

# Apply consistent text preprocessing
curl -X POST "http://localhost:8000/internal/cache/config/update" \
  -H "Content-Type: application/json" \
  -d '{
    "text_hash_threshold": 1000,
    "normalize_text": true,
    "consistent_encoding": "utf-8"
  }'

# Test key generation consistency
curl -X POST "http://localhost:8000/internal/cache/key-generator/test-consistency"
```

**Optimize TTL Configuration**:
```bash
# Apply operation-specific TTLs based on analysis
curl -X POST "http://localhost:8000/internal/cache/config/update" \
  -H "Content-Type: application/json" \
  -d '{
    "operation_ttls": {
      "summarize": 7200,
      "sentiment": 86400,
      "key_points": 7200,
      "questions": 3600,
      "qa": 1800
    },
    "default_ttl": 3600
  }'
```

**Improve Text Preprocessing**:
```bash
# Enable advanced text normalization
curl -X POST "http://localhost:8000/internal/cache/text-processor/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "enable_normalization": true,
    "strip_whitespace": true,
    "lowercase_processing": false,
    "remove_special_chars": false
  }'
```

### Issue 2: High Memory Usage (>100MB)

#### Symptoms
- Memory usage exceeding configured limits
- Out of memory warnings or errors
- Cache eviction happening frequently
- System performance degradation

#### Diagnostic Workflow
```bash
# Step 1: Memory usage breakdown
curl -s "http://localhost:8000/internal/cache/memory-analysis" | jq '{
  total_usage_mb: .total_memory_mb,
  l1_cache_usage: .l1_cache_memory_mb,
  monitoring_overhead: .monitoring_memory_mb,
  compression_buffer: .compression_buffer_mb,
  growth_trend: .memory_growth_trend
}'

# Step 2: Identify memory-intensive operations
curl -s "http://localhost:8000/internal/cache/memory-intensive-ops" | jq '{
  large_entries: .entries | map(select(.size_mb > 1)) | sort_by(-.size_mb),
  memory_by_operation: .operation_memory_usage,
  eviction_frequency: .eviction_stats
}'

# Step 3: Check compression effectiveness
curl -s "http://localhost:8000/internal/cache/compression-effectiveness" | jq '{
  compression_ratio: .avg_compression_ratio,
  uncompressed_entries: .uncompressed_count,
  compression_threshold: .current_threshold,
  potential_savings: .potential_memory_savings_mb
}'
```

#### Root Cause Analysis

**Large Uncompressed Entries**:
```bash
# Find large uncompressed entries
curl -s "http://localhost:8000/internal/cache/large-entries" | jq '{
  uncompressed_large: .entries | map(select(.compressed == false and .size_mb > 0.5)),
  compression_candidates: .compression_candidates,
  threshold_analysis: .threshold_effectiveness
}'
```

**Memory Leak Detection**:
```bash
# Check for memory growth patterns
curl -s "http://localhost:8000/internal/cache/memory-leak-analysis" | jq '{
  growth_rate_mb_per_hour: .growth_rate,
  memory_cleanup_effectiveness: .cleanup_stats,
  potential_leaks: .leak_indicators
}'
```

#### Resolution Steps

**Enable Aggressive Compression**:
```bash
# Lower compression threshold and increase level
curl -X POST "http://localhost:8000/internal/cache/config/update" \
  -H "Content-Type: application/json" \
  -d '{
    "compression_threshold": 500,
    "compression_level": 8,
    "force_compression_large_entries": true
  }'

# Compress existing large entries
curl -X POST "http://localhost:8000/internal/cache/compress-existing"
```

**Optimize Memory Cache Size**:
```bash
# Reduce memory cache size
curl -X POST "http://localhost:8000/internal/cache/config/update" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_cache_size": 100,
    "enable_aggressive_eviction": true,
    "memory_pressure_threshold": 50
  }'
```

**Implement Memory Cleanup**:
```bash
# Force immediate cleanup
curl -X POST "http://localhost:8000/internal/cache/memory-cleanup"

# Configure automatic cleanup
curl -X POST "http://localhost:8000/internal/cache/config/update" \
  -H "Content-Type: application/json" \
  -d '{
    "enable_automatic_cleanup": true,
    "cleanup_interval_minutes": 15,
    "memory_cleanup_threshold_mb": 75
  }'
```

### Issue 3: Slow Cache Operations (>50ms)

#### Symptoms
- Cache operations taking longer than expected
- High latency in API responses
- Performance degradation under load
- Timeout errors in cache operations

#### Diagnostic Workflow
```bash
# Step 1: Operation timing analysis
curl -s "http://localhost:8000/internal/cache/timing-analysis" | jq '{
  avg_get_time: .operations.get.avg_duration_ms,
  avg_set_time: .operations.set.avg_duration_ms,
  slow_operations: .operations | to_entries | map(select(.value.avg_duration_ms > 50)),
  p95_latency: .latency_percentiles.p95,
  p99_latency: .latency_percentiles.p99
}'

# Step 2: Redis connection performance
curl -s "http://localhost:8000/internal/cache/redis-performance" | jq '{
  connection_pool_usage: .connection_pool_stats,
  redis_response_time: .redis_avg_response_time,
  network_latency: .network_latency_ms,
  redis_cpu_usage: .redis_server_stats.cpu_usage
}'

# Step 3: Compression/decompression timing
curl -s "http://localhost:8000/internal/cache/compression-timing" | jq '{
  avg_compression_time: .compression.avg_time_ms,
  avg_decompression_time: .decompression.avg_time_ms,
  compression_overhead: .compression_cpu_overhead,
  slow_compression_entries: .slow_compression_operations
}'
```

#### Resolution Steps

**Optimize Redis Connection**:
```bash
# Tune connection pool settings
curl -X POST "http://localhost:8000/internal/cache/redis-config/update" \
  -H "Content-Type: application/json" \
  -d '{
    "max_connections": 20,
    "connection_timeout": 5,
    "retry_on_timeout": true,
    "socket_keepalive": true
  }'
```

**Optimize Compression Settings**:
```bash
# Balance compression ratio vs speed
curl -X POST "http://localhost:8000/internal/cache/config/update" \
  -H "Content-Type: application/json" \
  -d '{
    "compression_level": 6,
    "compression_threshold": 1000,
    "streaming_compression": true
  }'
```

**Enable Performance Optimizations**:
```bash
# Apply performance-focused configuration
curl -X POST "http://localhost:8000/internal/cache/config/apply-preset" \
  -H "Content-Type: application/json" \
  -d '{"preset": "performance"}'
```

## Systematic Troubleshooting

### Troubleshooting Decision Tree

```
Cache Performance Issue
├── Hit Rate < 50%
│   ├── Check Key Generation Consistency
│   ├── Review TTL Configuration
│   ├── Analyze Text Preprocessing
│   └── Examine Cache Invalidation
├── Memory Usage > 100MB
│   ├── Enable/Optimize Compression
│   ├── Reduce Memory Cache Size
│   ├── Check for Memory Leaks
│   └── Implement Cleanup Procedures
├── Operations > 50ms
│   ├── Optimize Redis Connection
│   ├── Tune Compression Settings
│   ├── Check Network Latency
│   └── Analyze Redis Performance
└── Redis Connection Issues
    ├── Verify Network Connectivity
    ├── Check Authentication
    ├── Test Fallback Mode
    └── Review Redis Server Status
```

### Step-by-Step Diagnostic Procedure

#### Phase 1: System Health Assessment (5 minutes)

```bash
# 1. Basic connectivity test
echo "Testing cache connectivity..."
curl -f "http://localhost:8000/internal/cache/health" || echo "❌ Cache unreachable"

# 2. Performance baseline
echo "Getting performance baseline..."
BASELINE=$(curl -s "http://localhost:8000/internal/cache/metrics")
echo $BASELINE | jq '{hit_rate: .cache_hit_rate, operations: .total_operations, memory_mb: .memory_usage.total_mb}'

# 3. Error detection
echo "Checking for recent errors..."
curl -s "http://localhost:8000/internal/cache/recent-errors" | jq '.errors[] | {timestamp, error_type, message}'
```

#### Phase 2: Detailed Analysis (10 minutes)

```bash
# 1. Performance deep dive
echo "Analyzing performance patterns..."
curl -s "http://localhost:8000/internal/cache/performance-analysis" | jq '{
  l1_performance: .l1_cache_stats,
  l2_performance: .l2_cache_stats,
  bottlenecks: .identified_bottlenecks,
  recommendations: .optimization_recommendations
}'

# 2. Configuration validation
echo "Validating configuration..."
curl -s "http://localhost:8000/internal/cache/config/validate" | jq '{
  config_valid: .is_valid,
  warnings: .warnings,
  errors: .errors,
  recommendations: .recommendations
}'

# 3. Resource utilization
echo "Checking resource utilization..."
curl -s "http://localhost:8000/internal/cache/resource-usage" | jq '{
  cpu_usage: .cpu_utilization,
  memory_usage: .memory_utilization,
  network_io: .network_stats,
  disk_io: .redis_disk_stats
}'
```

#### Step 3: Root Cause Identification (5 minutes)

```bash
# 1. Pattern analysis
echo "Analyzing usage patterns..."
curl -s "http://localhost:8000/internal/cache/pattern-analysis" | jq '{
  access_patterns: .access_pattern_analysis,
  temporal_patterns: .temporal_access_patterns,
  size_patterns: .data_size_patterns,
  anomalies: .detected_anomalies
}'

# 2. Correlation analysis
echo "Checking correlation with external factors..."
curl -s "http://localhost:8000/internal/cache/correlation-analysis" | jq '{
  redis_server_correlation: .redis_health_correlation,
  system_load_correlation: .system_load_impact,
  concurrent_requests: .concurrency_impact
}'
```

## Optimization Strategies

### Hit Rate Optimization

#### Text Preprocessing Optimization
```bash
# Implement consistent text normalization
curl -X POST "http://localhost:8000/internal/cache/optimize/text-processing" \
  -H "Content-Type: application/json" \
  -d '{
    "normalize_whitespace": true,
    "consistent_encoding": "utf-8",
    "remove_invisible_chars": true,
    "standardize_line_endings": true
  }'
```

#### Key Generation Optimization  
```bash
# Optimize key generation for better consistency
curl -X POST "http://localhost:8000/internal/cache/optimize/key-generation" \
  -H "Content-Type: application/json" \
  -d '{
    "hash_algorithm": "sha256",
    "text_size_thresholds": {
      "small": 500,
      "medium": 5000,
      "large": 50000
    },
    "option_normalization": true
  }'
```

#### TTL Strategy Optimization
```bash
# Apply intelligent TTL strategies based on content analysis
curl -X POST "http://localhost:8000/internal/cache/optimize/ttl-strategy" \
  -H "Content-Type: application/json" \
  -d '{
    "analyze_content_stability": true,
    "operation_specific_ttls": true,
    "dynamic_ttl_adjustment": true,
    "min_ttl": 300,
    "max_ttl": 86400
  }'
```

### Memory Management Optimization

#### Intelligent Compression Tuning
```bash
# Optimize compression based on usage patterns
curl -X POST "http://localhost:8000/internal/cache/optimize/compression" \
  -H "Content-Type: application/json" \
  -d '{
    "analyze_size_distribution": true,
    "optimize_threshold": true,
    "balance_ratio_vs_speed": true,
    "target_compression_ratio": 0.65
  }'
```

#### Memory Tier Optimization
```bash
# Optimize memory/Redis tier distribution
curl -X POST "http://localhost:8000/internal/cache/optimize/memory-tiers" \
  -H "Content-Type: application/json" \
  -d '{
    "analyze_access_patterns": true,
    "optimize_l1_size": true,
    "tune_promotion_strategy": true,
    "enable_predictive_loading": true
  }'
```

### Performance Tuning

#### Redis Connection Optimization
```bash
# Optimize Redis connection parameters
curl -X POST "http://localhost:8000/internal/cache/optimize/redis-connection" \
  -H "Content-Type: application/json" \
  -d '{
    "tune_connection_pool": true,
    "optimize_timeouts": true,
    "enable_pipelining": true,
    "connection_health_monitoring": true
  }'
```

#### Operation Batching
```bash
# Enable operation batching for better performance
curl -X POST "http://localhost:8000/internal/cache/optimize/batching" \
  -H "Content-Type: application/json" \
  -d '{
    "enable_bulk_operations": true,
    "batch_size_optimization": true,
    "intelligent_batching": true,
    "batch_timeout_ms": 100
  }'
```

## Configuration Troubleshooting

### Common Configuration Issues

#### Environment Variable Problems
```bash
# Validate environment configuration
curl -s "http://localhost:8000/internal/cache/config/environment-validation" | jq '{
  missing_variables: .missing_env_vars,
  invalid_values: .invalid_values,
  recommendations: .configuration_recommendations
}'
```

#### Preset Configuration Issues
```bash
# Verify preset application
curl -s "http://localhost:8000/internal/cache/config/preset-validation" | jq '{
  current_preset: .active_preset,
  preset_valid: .preset_validation_result,
  conflicts: .configuration_conflicts,
  overrides: .custom_overrides
}'
```

### Configuration Reset Procedures

#### Safe Configuration Reset
```bash
# Save current configuration
curl -s "http://localhost:8000/internal/cache/config/backup" > cache_config_backup.json

# Reset to known-good configuration
curl -X POST "http://localhost:8000/internal/cache/config/reset-to-default"

# Apply appropriate preset
curl -X POST "http://localhost:8000/internal/cache/config/apply-preset" \
  -H "Content-Type: application/json" \
  -d '{"preset": "production"}'

# Verify configuration
curl -s "http://localhost:8000/internal/cache/config/validate" | jq '.is_valid'
```

## Redis Connection Issues

### Connection Failure Diagnosis

#### Network Connectivity Testing
```bash
# Test Redis server reachability
echo "Testing Redis connectivity..."

# Extract Redis URL from cache config
REDIS_URL=$(curl -s "http://localhost:8000/internal/cache/config/current" | jq -r '.redis_url')
REDIS_HOST=$(echo $REDIS_URL | sed 's/redis:\/\/\([^:]*\).*/\1/')
REDIS_PORT=$(echo $REDIS_URL | sed 's/.*:\([0-9]*\).*/\1/')

# Network tests
ping -c 3 $REDIS_HOST || echo "❌ Host unreachable"
nc -z -v $REDIS_HOST $REDIS_PORT || echo "❌ Port closed"
redis-cli -h $REDIS_HOST -p $REDIS_PORT ping || echo "❌ Redis not responding"
```

#### Authentication Issues
```bash
# Test Redis authentication
curl -s "http://localhost:8000/internal/cache/redis/auth-test" | jq '{
  auth_configured: .auth_enabled,
  auth_successful: .auth_test_result,
  auth_method: .authentication_method,
  permissions: .user_permissions
}'
```

### Fallback Mode Verification

#### Memory-Only Mode Testing
```bash
# Test cache fallback functionality
echo "Testing cache fallback to memory-only mode..."

# Simulate Redis failure and test fallback
curl -X POST "http://localhost:8000/internal/cache/test-fallback" \
  -H "Content-Type: application/json" \
  -d '{"simulate_redis_failure": true}'

# Verify memory-only operations
curl -X POST "http://localhost:8000/internal/cache/test-memory-only" \
  -H "Content-Type: application/json" \
  -d '{
    "test_operations": ["get", "set", "delete"],
    "test_data_size": "medium"
  }' | jq '{
    memory_mode_active: .fallback_active,
    operations_successful: .test_results,
    performance: .performance_metrics
  }'
```

### Redis Recovery Procedures

#### Connection Recovery
```bash
# Attempt Redis reconnection
curl -X POST "http://localhost:8000/internal/cache/redis/reconnect"

# Check connection health after recovery
curl -s "http://localhost:8000/internal/cache/redis/health" | jq '{
  connected: .connection_status,
  response_time: .ping_response_time,
  memory_usage: .redis_memory_info,
  client_connections: .connected_clients
}'
```

#### Redis Configuration Optimization
```bash
# Apply Redis server optimizations
curl -X POST "http://localhost:8000/internal/cache/redis/optimize-server" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_policy": "allkeys-lru",
    "max_memory": "1gb",
    "timeout": 300,
    "tcp_keepalive": 60
  }'
```

## Memory Management

### Memory Usage Analysis

#### Memory Allocation Breakdown
```bash
# Detailed memory usage analysis
curl -s "http://localhost:8000/internal/cache/memory/detailed-analysis" | jq '{
  total_allocated_mb: .total_memory_mb,
  breakdown: {
    l1_cache_mb: .l1_cache_memory,
    redis_connection_mb: .redis_client_memory,
    monitoring_mb: .monitoring_overhead,
    compression_buffers_mb: .compression_memory,
    key_index_mb: .key_index_memory
  },
  growth_analysis: {
    hourly_growth_mb: .memory_growth_per_hour,
    projected_usage_24h: .projected_memory_24h,
    growth_trend: .growth_trend_classification
  }
}'
```

#### Memory Leak Detection
```bash
# Run memory leak analysis
curl -X POST "http://localhost:8000/internal/cache/memory/leak-analysis" | jq '{
  leak_indicators: .potential_leaks,
  memory_retention_issues: .retention_problems,
  cleanup_effectiveness: .cleanup_analysis,
  recommendations: .memory_optimization_recommendations
}'
```

### Memory Optimization Strategies

#### Aggressive Memory Cleanup
```bash
# Force comprehensive memory cleanup
curl -X POST "http://localhost:8000/internal/cache/memory/aggressive-cleanup" \
  -H "Content-Type: application/json" \
  -d '{
    "clear_expired_entries": true,
    "compress_large_entries": true,
    "garbage_collect": true,
    "optimize_data_structures": true
  }'

# Verify cleanup effectiveness
curl -s "http://localhost:8000/internal/cache/memory/cleanup-results" | jq '{
  memory_freed_mb: .memory_freed,
  entries_removed: .entries_cleaned,
  compression_applied: .newly_compressed_entries,
  final_usage_mb: .current_memory_usage
}'
```

#### Memory Pressure Response
```bash
# Configure automatic memory pressure handling
curl -X POST "http://localhost:8000/internal/cache/memory/pressure-config" \
  -H "Content-Type: application/json" \
  -d '{
    "enable_automatic_cleanup": true,
    "memory_pressure_threshold": 75,
    "cleanup_strategy": "lru_with_compression",
    "emergency_eviction_threshold": 90,
    "monitoring_interval_seconds": 30
  }'
```

## Health Check Integration

### Comprehensive Health Monitoring

#### Multi-Level Health Assessment
```bash
# Comprehensive cache health check
curl -s "http://localhost:8000/internal/cache/health/comprehensive" | jq '{
  overall_health: .health_status,
  component_health: {
    l1_cache: .l1_cache_health,
    redis_connection: .redis_health,
    compression_system: .compression_health,
    monitoring: .monitoring_health,
    key_generator: .key_generator_health
  },
  performance_health: {
    hit_rate_status: .hit_rate_health,
    latency_status: .latency_health,
    memory_status: .memory_health,
    throughput_status: .throughput_health
  },
  alerts: .active_alerts
}'
```

#### Custom Health Checks
```bash
# Configure custom health check thresholds
curl -X POST "http://localhost:8000/internal/cache/health/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "thresholds": {
      "hit_rate_warning": 0.6,
      "hit_rate_critical": 0.4,
      "memory_warning_mb": 50,
      "memory_critical_mb": 100,
      "latency_warning_ms": 20,
      "latency_critical_ms": 50
    },
    "check_intervals": {
      "performance_check_seconds": 30,
      "memory_check_seconds": 60,
      "connectivity_check_seconds": 120
    }
  }'
```

### Monitoring Integration

#### External Monitoring System Integration
```bash
# Export metrics for external monitoring
curl -s "http://localhost:8000/internal/cache/metrics/prometheus" > cache_metrics.prom

# Get monitoring integration status
curl -s "http://localhost:8000/internal/cache/monitoring/status" | jq '{
  monitoring_enabled: .monitoring_active,
  exporters_configured: .active_exporters,
  alerting_rules: .configured_alerts,
  dashboard_links: .monitoring_dashboards
}'
```

## Emergency Procedures

### Critical Issue Response

#### Complete Cache System Reset
```bash
# EMERGENCY: Complete cache reset procedure
echo "⚠️  EMERGENCY CACHE RESET PROCEDURE"
echo "This will clear all cached data and reset configuration"
echo "Continue? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    # Step 1: Backup current configuration
    echo "Backing up configuration..."
    curl -s "http://localhost:8000/internal/cache/config/backup" > emergency_backup_$(date +%Y%m%d_%H%M%S).json
    
    # Step 2: Clear all cache data
    echo "Clearing cache data..."
    curl -X POST "http://localhost:8000/internal/cache/emergency/clear-all"
    
    # Step 3: Reset configuration to safe defaults
    echo "Resetting configuration..."
    curl -X POST "http://localhost:8000/internal/cache/emergency/reset-config"
    
    # Step 4: Restart cache services
    echo "Restarting cache services..."
    curl -X POST "http://localhost:8000/internal/cache/emergency/restart"
    
    # Step 5: Verify recovery
    echo "Verifying system recovery..."
    sleep 10
    curl -s "http://localhost:8000/internal/cache/health" | jq '.health_status'
    
    echo "✅ Emergency reset completed"
else
    echo "❌ Emergency reset cancelled"
fi
```

#### Cache Service Isolation
```bash
# Isolate cache service for emergency maintenance
curl -X POST "http://localhost:8000/internal/cache/emergency/isolate" \
  -H "Content-Type: application/json" \
  -d '{
    "disable_new_writes": true,
    "drain_existing_operations": true,
    "enable_maintenance_mode": true,
    "redirect_to_fallback": true
  }'

# Check isolation status
curl -s "http://localhost:8000/internal/cache/emergency/status" | jq '{
  isolated: .isolation_active,
  maintenance_mode: .maintenance_mode,
  pending_operations: .operations_pending,
  fallback_active: .fallback_mode_active
}'
```

### Disaster Recovery

#### Data Recovery Procedures
```bash
# Attempt cache data recovery from Redis
curl -X POST "http://localhost:8000/internal/cache/recovery/redis-data" \
  -H "Content-Type: application/json" \
  -d '{
    "recovery_strategy": "conservative",
    "validate_data_integrity": true,
    "recovery_batch_size": 100,
    "timeout_seconds": 300
  }' | jq '{
    recovery_successful: .recovery_completed,
    recovered_entries: .entries_recovered,
    failed_recoveries: .recovery_failures,
    data_integrity_status: .integrity_check_result
}'
```

#### Service Restoration
```bash
# Restore cache service after emergency
curl -X POST "http://localhost:8000/internal/cache/recovery/restore-service" \
  -H "Content-Type: application/json" \
  -d '{
    "restoration_strategy": "gradual",
    "health_check_required": true,
    "performance_validation": true,
    "rollback_on_failure": true
  }' | jq '{
    restoration_successful: .service_restored,
    health_check_passed: .health_validation,
    performance_acceptable: .performance_validation,
    rollback_triggered: .rollback_executed
}'
```

### Post-Emergency Analysis

#### Incident Analysis
```bash
# Generate post-incident report
curl -X POST "http://localhost:8000/internal/cache/analysis/post-incident" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_timeframe": "last_4_hours",
    "include_performance_data": true,
    "include_configuration_changes": true,
    "include_error_logs": true
  }' | jq '{
    incident_timeline: .timeline_analysis,
    root_cause_analysis: .identified_root_causes,
    impact_assessment: .business_impact,
    prevention_recommendations: .future_prevention_measures
}'
```

## Related Documentation

### ❗️ Prerequisites
> Complete these guides before using this troubleshooting guide.

- **[Cache Infrastructure Guide](./CACHE.md)**: Complete technical documentation and architecture overview
- **[Cache Usage Guide](./usage-guide.md)**: Understanding cache implementation and usage patterns  
- **[Cache Configuration Guide](./configuration.md)**: Configuration management and environment setup

### 🔗 Related Topics
> Explore these related guides for additional context and complementary information.

- **[Cache Testing Guide](./testing.md)**: Unit and integration tests
- **[Cache API Reference](./api-reference.md)**: Detailed API endpoints for diagnostics and management
- **[Monitoring Infrastructure](../MONITORING.md)**: Comprehensive monitoring that includes cache performance analytics
- **[Resilience Infrastructure](../RESILIENCE.md)**: Fault tolerance patterns that complement cache reliability
- **[General Troubleshooting Guide](../../operations/TROUBLESHOOTING.md)**: System-wide troubleshooting procedures

### ➡️ Next Steps
> Continue your journey with these advanced guides and practical applications.

- **[Performance Optimization Guide](../../operations/PERFORMANCE_OPTIMIZATION.md)**: Advanced cache optimization and tuning procedures
- **[Backup & Recovery Guide](../../operations/BACKUP_RECOVERY.md)**: Data backup and recovery procedures including cache data
- **[Security Guide](../../operations/SECURITY.md)**: Production security considerations for cache infrastructure
- **[Deployment Guide](../../developer/DEPLOYMENT.md)**: Production deployment considerations for caching infrastructure

---
*💡 **Need help?** Check the [Documentation Index](../../../DOCS_INDEX.md) for a complete overview of all available guides.*