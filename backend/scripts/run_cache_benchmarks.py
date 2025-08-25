from app.infrastructure.cache.benchmarks import CachePerformanceBenchmark
from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.redis_ai import AIResponseCache

# Initialize benchmark system
benchmark = CachePerformanceBenchmark()

# Benchmark basic cache operations
cache = GenericRedisCache()
result = await benchmark.benchmark_basic_operations(cache, iterations=100)
print(f"Average operation time: {result.avg_duration_ms:.2f}ms")
print(f"Operations per second: {result.operations_per_second:.0f}")

# Test memory cache performance
memory_result = await benchmark.benchmark_memory_cache_performance(cache)
print(f"L1 cache hit rate: {memory_result.cache_hit_rate:.1f}%")

# Compare implementations
old_cache = AIResponseCache()
comparison = await benchmark.compare_before_after_refactoring(old_cache, cache)
print(f"Performance change: {comparison.performance_change_percent:+.1f}%")

# Generate comprehensive report
suite = benchmark.run_comprehensive_benchmark_suite(cache)
report = benchmark.generate_performance_report(suite)
print(report)