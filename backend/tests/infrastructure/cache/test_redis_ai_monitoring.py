"""
Comprehensive tests for AIResponseCache AI-specific monitoring methods (Phase 2 Deliverable 6).

This module tests all 8 AI-specific monitoring methods implemented in the AIResponseCache:
1. get_ai_performance_summary()
2. get_text_tier_statistics()
3. _analyze_tier_performance()
4. get_operation_performance()
5. _record_ai_cache_hit()
6. _record_ai_cache_miss()
7. _record_operation_performance()
8. _generate_ai_optimization_recommendations()

Test Coverage Areas:
- Comprehensive monitoring functionality
- Performance analytics and metrics calculation
- Optimization recommendation generation
- Error handling and edge cases
- Integration with existing cache infrastructure
- Zero operations handling and data validation
"""

import pytest
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from app.core.exceptions import ConfigurationError, ValidationError
from app.infrastructure.cache.redis_ai import AIResponseCache
from app.infrastructure.cache.monitoring import CachePerformanceMonitor


class TestAIPerformanceSummary:
    """Test get_ai_performance_summary method."""

    @pytest.fixture
    def ai_cache_with_data(self):
        """Create AIResponseCache with sample performance data."""
        cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            performance_monitor=MagicMock(spec=CachePerformanceMonitor)
        )
        
        # Add sample metrics data
        cache.ai_metrics['cache_hits_by_operation']['summarize'] = 80
        cache.ai_metrics['cache_hits_by_operation']['sentiment'] = 45
        cache.ai_metrics['cache_misses_by_operation']['summarize'] = 20
        cache.ai_metrics['cache_misses_by_operation']['sentiment'] = 5
        cache.ai_metrics['text_tier_distribution']['small'] = 30
        cache.ai_metrics['text_tier_distribution']['medium'] = 60
        cache.ai_metrics['text_tier_distribution']['large'] = 35
        
        return cache

    def test_get_ai_performance_summary_basic_functionality(self, ai_cache_with_data):
        """Test basic AI performance summary generation."""
        with patch.object(ai_cache_with_data.key_generator, 'get_key_generation_stats', return_value={"avg_time": 0.005}):
            with patch.object(ai_cache_with_data, '_generate_ai_optimization_recommendations', return_value=[]):
                summary = ai_cache_with_data.get_ai_performance_summary()
                
                # Verify basic structure
                assert 'total_operations' in summary
                assert 'overall_hit_rate' in summary
                assert 'hit_rate_by_operation' in summary
                assert 'text_tier_distribution' in summary
                assert 'key_generation_stats' in summary
                assert 'optimization_recommendations' in summary
                assert 'inherited_stats' in summary
                
                # Verify calculations
                assert summary['total_operations'] == 150  # 80+45+20+5
                assert summary['overall_hit_rate'] == 83.33  # (80+45)/(80+45+20+5) * 100
                assert summary['hit_rate_by_operation']['summarize'] == 80.0  # 80/(80+20) * 100
                assert summary['hit_rate_by_operation']['sentiment'] == 90.0  # 45/(45+5) * 100

    def test_get_ai_performance_summary_zero_operations(self, ai_cache_with_data):
        """Test performance summary with zero operations."""
        # Clear all metrics
        ai_cache_with_data.ai_metrics['cache_hits_by_operation'].clear()
        ai_cache_with_data.ai_metrics['cache_misses_by_operation'].clear()
        
        with patch.object(ai_cache_with_data.key_generator, 'get_key_generation_stats', return_value={}):
            summary = ai_cache_with_data.get_ai_performance_summary()
            
            # Verify zero operations handling
            assert summary['total_operations'] == 0
            assert summary['overall_hit_rate'] == 0.0
            assert summary['hit_rate_by_operation'] == {}
            assert len(summary['optimization_recommendations']) == 0

    def test_get_ai_performance_summary_error_handling(self, ai_cache_with_data):
        """Test error handling in performance summary generation."""
        # Mock an error in key generation stats
        with patch.object(ai_cache_with_data.key_generator, 'get_key_generation_stats', side_effect=Exception("Test error")):
            summary = ai_cache_with_data.get_ai_performance_summary()
            
            # Should return error summary instead of raising
            assert 'error' in summary
            assert summary['total_operations'] == 0


class TestTextTierStatistics:
    """Test get_text_tier_statistics method."""

    @pytest.fixture  
    def ai_cache_with_tier_data(self):
        """Create AIResponseCache with tier-specific data."""
        cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            performance_monitor=MagicMock(spec=CachePerformanceMonitor),
            text_size_tiers={
                "small": 500,
                "medium": 5000,
                "large": 50000
            }
        )
        
        # Add tier distribution data
        cache.ai_metrics['text_tier_distribution']['small'] = 25
        cache.ai_metrics['text_tier_distribution']['medium'] = 40
        cache.ai_metrics['text_tier_distribution']['large'] = 15
        
        return cache

    def test_get_text_tier_statistics_basic_functionality(self, ai_cache_with_tier_data):
        """Test basic text tier statistics generation."""
        with patch.object(ai_cache_with_tier_data, '_analyze_tier_performance', return_value={"tier_hit_rates": {"small": 95.0}}):
            stats = ai_cache_with_tier_data.get_text_tier_statistics()
            
            # Verify structure
            assert 'tier_configuration' in stats
            assert 'tier_distribution' in stats
            assert 'tier_performance_analysis' in stats
            assert 'data_completeness' in stats
            
            # Verify tier configuration
            assert stats['tier_configuration']['small'] == 500
            assert stats['tier_configuration']['medium'] == 5000
            assert stats['tier_configuration']['large'] == 50000
            
            # Verify tier distribution
            assert stats['tier_distribution']['small'] == 25
            assert stats['tier_distribution']['medium'] == 40
            assert stats['tier_distribution']['large'] == 15

    def test_get_text_tier_statistics_data_completeness_validation(self, ai_cache_with_tier_data):
        """Test data completeness validation in tier statistics."""
        with patch.object(ai_cache_with_tier_data, '_analyze_tier_performance', return_value={}):
            stats = ai_cache_with_tier_data.get_text_tier_statistics()
            
            # Verify completeness analysis
            completeness = stats['data_completeness']
            assert 'expected_tiers' in completeness
            assert 'recorded_tiers' in completeness
            assert 'missing_tiers' in completeness
            assert 'completeness_percentage' in completeness
            
            # Should include xlarge in expected tiers
            assert 'xlarge' in completeness['expected_tiers']
            
            # Should add missing tiers with zero counts
            assert stats['tier_distribution']['xlarge'] == 0

    def test_get_text_tier_statistics_error_handling(self, ai_cache_with_tier_data):
        """Test error handling in tier statistics generation."""
        # Mock an error in tier configuration access
        with patch.object(ai_cache_with_tier_data.text_size_tiers, '__getitem__', side_effect=KeyError("test")):
            stats = ai_cache_with_tier_data.get_text_tier_statistics()
            
            # Should use fallback configuration
            assert stats['tier_configuration']['small'] == 500
            assert stats['tier_configuration']['medium'] == 5000
            assert stats['tier_configuration']['large'] == 50000


class TestOperationPerformance:
    """Test get_operation_performance method."""

    @pytest.fixture
    def ai_cache_with_performance_data(self):
        """Create AIResponseCache with operation performance data."""
        cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            performance_monitor=MagicMock(spec=CachePerformanceMonitor)
        )
        
        # Add sample operation performance data
        cache.ai_metrics['operation_performance'] = [
            {'operation': 'summarize', 'duration': 0.150, 'timestamp': time.time()},
            {'operation': 'summarize', 'duration': 0.120, 'timestamp': time.time()},
            {'operation': 'summarize', 'duration': 0.180, 'timestamp': time.time()},
            {'operation': 'sentiment', 'duration': 0.050, 'timestamp': time.time()},
            {'operation': 'sentiment', 'duration': 0.045, 'timestamp': time.time()},
        ]
        
        return cache

    def test_get_operation_performance_basic_functionality(self, ai_cache_with_performance_data):
        """Test basic operation performance metrics generation."""
        perf_data = ai_cache_with_performance_data.get_operation_performance()
        
        # Verify structure
        assert 'operations' in perf_data
        assert 'summary' in perf_data
        
        # Verify operation metrics
        summarize_metrics = perf_data['operations']['summarize']
        assert 'avg_duration_ms' in summarize_metrics
        assert 'min_duration_ms' in summarize_metrics
        assert 'max_duration_ms' in summarize_metrics
        assert 'percentiles' in summarize_metrics
        assert 'total_operations' in summarize_metrics
        assert 'configured_ttl' in summarize_metrics
        
        # Verify calculations (150ms, 120ms, 180ms -> avg 150ms)
        assert summarize_metrics['avg_duration_ms'] == 150.0
        assert summarize_metrics['min_duration_ms'] == 120.0
        assert summarize_metrics['max_duration_ms'] == 180.0
        assert summarize_metrics['total_operations'] == 3
        
        # Verify percentiles
        assert 'p50' in summarize_metrics['percentiles']
        assert 'p95' in summarize_metrics['percentiles'] 
        assert 'p99' in summarize_metrics['percentiles']

    def test_get_operation_performance_percentile_calculations(self, ai_cache_with_performance_data):
        """Test percentile calculations in operation performance."""
        perf_data = ai_cache_with_performance_data.get_operation_performance()
        
        # Test sentiment metrics (50ms, 45ms -> sorted: 45ms, 50ms)
        sentiment_metrics = perf_data['operations']['sentiment']
        percentiles = sentiment_metrics['percentiles']
        
        # For 2 items: p50 = item[1], p95 = item[1], p99 = item[1]
        assert percentiles['p50'] == 50.0  # 50ms converted to ms
        assert percentiles['p95'] == 50.0  # Last item for small dataset
        assert percentiles['p99'] == 50.0  # Last item for small dataset

    def test_get_operation_performance_no_data(self):
        """Test operation performance with no data."""
        cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            performance_monitor=MagicMock(spec=CachePerformanceMonitor)
        )
        
        perf_data = cache.get_operation_performance()
        
        # Should return empty but valid structure
        assert perf_data['operations'] == {}
        assert perf_data['summary']['total_operations_measured'] == 0
        assert perf_data['summary']['total_operation_types'] == 0


class TestAICacheHitRecording:
    """Test _record_ai_cache_hit method."""

    @pytest.fixture
    def ai_cache_for_recording(self):
        """Create AIResponseCache for recording tests."""
        return AIResponseCache(
            redis_url="redis://localhost:6379",
            performance_monitor=MagicMock(spec=CachePerformanceMonitor)
        )

    def test_record_ai_cache_hit_basic_functionality(self, ai_cache_for_recording):
        """Test basic AI cache hit recording."""
        ai_cache_for_recording._record_ai_cache_hit(
            cache_type="l1",
            text="Sample text content",
            operation="summarize",
            text_tier="medium"
        )
        
        # Verify performance monitor was called
        ai_cache_for_recording.performance_monitor.record_cache_operation_time.assert_called_once()
        call_args = ai_cache_for_recording.performance_monitor.record_cache_operation_time.call_args
        
        assert call_args[1]['operation'] == "get"
        assert call_args[1]['cache_hit'] is True
        assert call_args[1]['additional_data']['cache_type'] == "l1"
        assert call_args[1]['additional_data']['ai_operation'] == "summarize"
        assert call_args[1]['additional_data']['text_tier'] == "medium"
        
        # Verify internal metrics were updated
        assert ai_cache_for_recording.ai_metrics['cache_hits_by_operation']['summarize'] == 1
        assert ai_cache_for_recording.ai_metrics['text_tier_distribution']['medium'] == 1
        assert ai_cache_for_recording.ai_metrics['cache_hits_by_type']['l1'] == 1

    def test_record_ai_cache_hit_input_validation(self, ai_cache_for_recording):
        """Test input validation in AI cache hit recording."""
        # Test invalid cache_type
        ai_cache_for_recording._record_ai_cache_hit(
            cache_type="",
            text="text",
            operation="summarize",
            text_tier="small"
        )
        
        # Should not call performance monitor due to validation failure
        ai_cache_for_recording.performance_monitor.record_cache_operation_time.assert_not_called()

    def test_record_ai_cache_hit_error_handling(self, ai_cache_for_recording):
        """Test error handling in AI cache hit recording."""
        # Mock performance monitor to raise error
        ai_cache_for_recording.performance_monitor.record_cache_operation_time.side_effect = Exception("Test error")
        
        # Should not raise exception
        ai_cache_for_recording._record_ai_cache_hit(
            cache_type="redis",
            text="text",
            operation="summarize",
            text_tier="small"
        )


class TestAICacheMissRecording:
    """Test _record_ai_cache_miss method."""

    @pytest.fixture
    def ai_cache_for_recording(self):
        """Create AIResponseCache for recording tests."""
        return AIResponseCache(
            redis_url="redis://localhost:6379",
            performance_monitor=MagicMock(spec=CachePerformanceMonitor)
        )

    def test_record_ai_cache_miss_basic_functionality(self, ai_cache_for_recording):
        """Test basic AI cache miss recording."""
        ai_cache_for_recording._record_ai_cache_miss(
            text="New content not in cache",
            operation="sentiment",
            text_tier="small"
        )
        
        # Verify performance monitor was called
        ai_cache_for_recording.performance_monitor.record_cache_operation_time.assert_called_once()
        call_args = ai_cache_for_recording.performance_monitor.record_cache_operation_time.call_args
        
        assert call_args[1]['operation'] == "get"
        assert call_args[1]['cache_hit'] is False
        assert call_args[1]['additional_data']['ai_operation'] == "sentiment"
        assert call_args[1]['additional_data']['text_tier'] == "small"
        assert call_args[1]['additional_data']['cache_result'] == "miss"
        
        # Verify internal metrics were updated
        assert ai_cache_for_recording.ai_metrics['cache_misses_by_operation']['sentiment'] == 1
        assert ai_cache_for_recording.ai_metrics['text_tier_distribution']['small'] == 1
        assert ai_cache_for_recording.ai_metrics['cache_miss_reasons']['key_not_found'] == 1

    def test_record_ai_cache_miss_input_validation(self, ai_cache_for_recording):
        """Test input validation in AI cache miss recording."""
        # Test invalid operation
        ai_cache_for_recording._record_ai_cache_miss(
            text="text",
            operation="",
            text_tier="small"
        )
        
        # Should not call performance monitor due to validation failure
        ai_cache_for_recording.performance_monitor.record_cache_operation_time.assert_not_called()


class TestOperationPerformanceRecording:
    """Test _record_operation_performance method."""

    @pytest.fixture
    def ai_cache_for_recording(self):
        """Create AIResponseCache for recording tests."""
        return AIResponseCache(
            redis_url="redis://localhost:6379",
            performance_monitor=MagicMock(spec=CachePerformanceMonitor)
        )

    def test_record_operation_performance_basic_functionality(self, ai_cache_for_recording):
        """Test basic operation performance recording."""
        ai_cache_for_recording._record_operation_performance("summarize", 0.125)
        
        # Verify operation was recorded
        assert len(ai_cache_for_recording.ai_metrics['operation_performance']) == 1
        
        record = ai_cache_for_recording.ai_metrics['operation_performance'][0]
        assert record['operation'] == "summarize"
        assert record['duration'] == 0.125
        assert record['duration_ms'] == 125.0
        assert 'timestamp' in record
        assert 'iso_timestamp' in record
        
        # Verify running totals
        assert ai_cache_for_recording.ai_metrics['operation_duration_totals']['summarize'] == 0.125
        assert ai_cache_for_recording.ai_metrics['operation_count_totals']['summarize'] == 1

    def test_record_operation_performance_memory_management(self, ai_cache_for_recording):
        """Test memory management in operation performance recording."""
        # Add more than 1000 records to test trimming
        for i in range(1005):
            ai_cache_for_recording._record_operation_performance(f"operation_{i % 5}", 0.001)
        
        # Should be trimmed to 1000 records
        assert len(ai_cache_for_recording.ai_metrics['operation_performance']) == 1000

    def test_record_operation_performance_input_validation(self, ai_cache_for_recording):
        """Test input validation in operation performance recording."""
        # Test invalid operation_type
        ai_cache_for_recording._record_operation_performance("", 0.1)
        assert len(ai_cache_for_recording.ai_metrics['operation_performance']) == 0
        
        # Test invalid duration
        ai_cache_for_recording._record_operation_performance("test", -1.0)
        assert len(ai_cache_for_recording.ai_metrics['operation_performance']) == 0


class TestOptimizationRecommendations:
    """Test _generate_ai_optimization_recommendations method."""

    @pytest.fixture
    def ai_cache_with_recommendation_data(self):
        """Create AIResponseCache with data for recommendation testing."""
        cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            performance_monitor=MagicMock(spec=CachePerformanceMonitor),
            memory_cache_size=100
        )
        
        # Add data for various recommendation scenarios
        cache.ai_metrics['cache_hits_by_operation']['low_hit_op'] = 2
        cache.ai_metrics['cache_misses_by_operation']['low_hit_op'] = 8  # 20% hit rate
        cache.ai_metrics['cache_hits_by_operation']['high_hit_op'] = 19
        cache.ai_metrics['cache_misses_by_operation']['high_hit_op'] = 1  # 95% hit rate
        
        cache.ai_metrics['text_tier_distribution']['xlarge'] = 50  # High proportion
        cache.ai_metrics['text_tier_distribution']['small'] = 5   # Low proportion
        cache.ai_metrics['text_tier_distribution']['total'] = 100
        
        # Mock memory cache to be near capacity
        with patch.object(cache, 'memory_cache', {'item1': 'data1', 'item2': 'data2'}):
            cache._memory_cache_mock = {'item1': 'data1', 'item2': 'data2'}
        
        return cache

    def test_generate_ai_optimization_recommendations_low_hit_rate(self, ai_cache_with_recommendation_data):
        """Test recommendations for low hit rate operations."""
        recommendations = ai_cache_with_recommendation_data._generate_ai_optimization_recommendations()
        
        # Should have recommendation for low hit rate operation
        low_hit_recs = [r for r in recommendations if r['type'] == 'hit_rate' and 'low_hit_op' in r['title']]
        assert len(low_hit_recs) > 0
        
        low_hit_rec = low_hit_recs[0]
        assert low_hit_rec['priority'] == 'high'
        assert 'Low hit rate' in low_hit_rec['title']
        assert '20.0%' in low_hit_rec['description']

    def test_generate_ai_optimization_recommendations_high_hit_rate(self, ai_cache_with_recommendation_data):
        """Test recommendations for high hit rate operations."""
        recommendations = ai_cache_with_recommendation_data._generate_ai_optimization_recommendations()
        
        # Should have recommendation for high hit rate operation
        high_hit_recs = [r for r in recommendations if r['type'] == 'hit_rate' and 'high_hit_op' in r['title']]
        assert len(high_hit_recs) > 0
        
        high_hit_rec = high_hit_recs[0]
        assert high_hit_rec['priority'] == 'low'
        assert 'Excellent hit rate' in high_hit_rec['title']
        assert '95.0%' in high_hit_rec['description']

    def test_generate_ai_optimization_recommendations_text_tier_analysis(self, ai_cache_with_recommendation_data):
        """Test recommendations based on text tier distribution."""
        recommendations = ai_cache_with_recommendation_data._generate_ai_optimization_recommendations()
        
        # Should have recommendations for tier distribution issues
        tier_recs = [r for r in recommendations if r['type'] == 'text_tier']
        assert len(tier_recs) > 0

    def test_generate_ai_optimization_recommendations_priority_sorting(self, ai_cache_with_recommendation_data):
        """Test that recommendations are sorted by priority."""
        recommendations = ai_cache_with_recommendation_data._generate_ai_optimization_recommendations()
        
        # Should be sorted: high -> medium -> low
        priorities = [r['priority'] for r in recommendations]
        high_indices = [i for i, p in enumerate(priorities) if p == 'high']
        medium_indices = [i for i, p in enumerate(priorities) if p == 'medium']
        low_indices = [i for i, p in enumerate(priorities) if p == 'low']
        
        # All high priority should come before medium, medium before low
        if high_indices and medium_indices:
            assert max(high_indices) < min(medium_indices)
        if medium_indices and low_indices:
            assert max(medium_indices) < min(low_indices)

    def test_generate_ai_optimization_recommendations_error_handling(self, ai_cache_with_recommendation_data):
        """Test error handling in recommendation generation."""
        # Mock an error in metrics access
        with patch.object(ai_cache_with_recommendation_data.ai_metrics['cache_hits_by_operation'], 'keys', side_effect=Exception("Test error")):
            recommendations = ai_cache_with_recommendation_data._generate_ai_optimization_recommendations()
            
            # Should return error recommendation instead of raising
            assert len(recommendations) == 1
            assert recommendations[0]['type'] == 'error'
            assert recommendations[0]['priority'] == 'high'


class TestTierPerformanceAnalysis:
    """Test _analyze_tier_performance helper method."""

    @pytest.fixture
    def ai_cache_with_tier_performance_data(self):
        """Create AIResponseCache with tier performance data."""
        cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            performance_monitor=MagicMock(spec=CachePerformanceMonitor)
        )
        
        # Add tier distribution
        cache.ai_metrics['text_tier_distribution']['small'] = 20
        cache.ai_metrics['text_tier_distribution']['medium'] = 30
        cache.ai_metrics['text_tier_distribution']['large'] = 15
        
        # Add operation performance data with tier information
        cache.ai_metrics['operation_performance'] = [
            {
                'text_tier': 'small',
                'cache_operation': 'get',
                'success': True,
                'duration': 0.010,
                'operation': 'summarize'
            },
            {
                'text_tier': 'small',
                'cache_operation': 'get',
                'success': True,
                'duration': 0.008,
                'operation': 'sentiment'
            },
            {
                'text_tier': 'medium',
                'cache_operation': 'get',
                'success': False,
                'duration': 0.050,
                'operation': 'summarize'
            },
            {
                'text_tier': 'medium',
                'cache_operation': 'get',
                'success': True,
                'duration': 0.045,
                'operation': 'sentiment'
            },
        ]
        
        return cache

    def test_analyze_tier_performance_basic_functionality(self, ai_cache_with_tier_performance_data):
        """Test basic tier performance analysis."""
        analysis = ai_cache_with_tier_performance_data._analyze_tier_performance()
        
        # Verify structure
        assert 'tier_hit_rates' in analysis
        assert 'average_response_times' in analysis
        assert 'tier_optimization_opportunities' in analysis
        assert 'performance_rankings' in analysis
        
        # Verify hit rate calculations
        # Small tier: 2 hits, 0 misses = 100% hit rate
        assert analysis['tier_hit_rates']['small'] == 100.0
        # Medium tier: 1 hit, 1 miss = 50% hit rate
        assert analysis['tier_hit_rates']['medium'] == 50.0

    def test_analyze_tier_performance_response_time_calculations(self, ai_cache_with_tier_performance_data):
        """Test response time calculations in tier analysis."""
        analysis = ai_cache_with_tier_performance_data._analyze_tier_performance()
        
        # Small tier: (10ms + 8ms) / 2 = 9ms average
        small_times = analysis['average_response_times']['small']
        assert small_times['avg_ms'] == 9.0
        assert small_times['min_ms'] == 8.0
        assert small_times['max_ms'] == 10.0
        assert small_times['sample_count'] == 2

    def test_analyze_tier_performance_optimization_opportunities(self, ai_cache_with_tier_performance_data):
        """Test optimization opportunity generation in tier analysis."""
        analysis = ai_cache_with_tier_performance_data._analyze_tier_performance()
        
        # Should have optimization opportunities
        assert 'small' in analysis['tier_optimization_opportunities']
        assert 'medium' in analysis['tier_optimization_opportunities']
        
        # Small tier should have excellent hit rate message
        small_opportunities = analysis['tier_optimization_opportunities']['small']
        excellent_msgs = [opp for opp in small_opportunities if 'Excellent hit rate' in opp]
        assert len(excellent_msgs) > 0

    def test_analyze_tier_performance_rankings(self, ai_cache_with_tier_performance_data):
        """Test performance rankings in tier analysis."""
        analysis = ai_cache_with_tier_performance_data._analyze_tier_performance()
        
        rankings = analysis['performance_rankings']
        assert len(rankings) > 0
        
        # Should be sorted by performance score (descending)
        scores = [r['performance_score'] for r in rankings]
        assert scores == sorted(scores, reverse=True)
        
        # Each ranking should have required fields
        for ranking in rankings:
            assert 'tier' in ranking
            assert 'hit_rate' in ranking
            assert 'avg_response_time_ms' in ranking
            assert 'performance_score' in ranking

    def test_analyze_tier_performance_error_handling(self, ai_cache_with_tier_performance_data):
        """Test error handling in tier performance analysis."""
        # Mock an error in tier distribution access
        with patch.object(ai_cache_with_tier_performance_data.ai_metrics['text_tier_distribution'], 'keys', side_effect=Exception("Test error")):
            analysis = ai_cache_with_tier_performance_data._analyze_tier_performance()
            
            # Should return error analysis instead of raising
            assert 'error' in analysis
            assert analysis['tier_hit_rates'] == {}


# Integration Tests
class TestMonitoringIntegration:
    """Test integration between monitoring methods and existing cache infrastructure."""

    @pytest.fixture
    def integrated_ai_cache(self):
        """Create AIResponseCache with realistic integrated data."""
        cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            performance_monitor=MagicMock(spec=CachePerformanceMonitor),
            text_size_tiers={
                "small": 300,
                "medium": 3000,
                "large": 30000
            }
        )
        
        # Simulate realistic cache operations
        operations = ['summarize', 'sentiment', 'key_points', 'qa']
        for i in range(50):
            op = operations[i % len(operations)]
            tier = ['small', 'medium', 'large'][i % 3]
            success = i % 4 != 0  # 75% hit rate
            
            if success:
                cache.ai_metrics['cache_hits_by_operation'][op] += 1
            else:
                cache.ai_metrics['cache_misses_by_operation'][op] += 1
            
            cache.ai_metrics['text_tier_distribution'][tier] += 1
            cache.ai_metrics['operation_performance'].append({
                'operation': op,
                'text_tier': tier,
                'cache_operation': 'get',
                'success': success,
                'duration': 0.020 + (i * 0.001),  # Increasing duration
                'timestamp': time.time() - (50 - i)
            })
        
        return cache

    def test_comprehensive_monitoring_workflow(self, integrated_ai_cache):
        """Test complete monitoring workflow with all methods."""
        # Test performance summary
        summary = integrated_ai_cache.get_ai_performance_summary()
        assert summary['total_operations'] > 0
        assert 0 <= summary['overall_hit_rate'] <= 100
        
        # Test tier statistics  
        tier_stats = integrated_ai_cache.get_text_tier_statistics()
        assert len(tier_stats['tier_distribution']) > 0
        assert tier_stats['data_completeness']['completeness_percentage'] > 0
        
        # Test operation performance
        op_perf = integrated_ai_cache.get_operation_performance()
        assert len(op_perf['operations']) > 0
        assert op_perf['summary']['total_operations_measured'] > 0
        
        # Test that all methods work together without conflicts
        assert summary is not None
        assert tier_stats is not None  
        assert op_perf is not None

    def test_monitoring_methods_consistency(self, integrated_ai_cache):
        """Test consistency between different monitoring methods."""
        summary = integrated_ai_cache.get_ai_performance_summary()
        tier_stats = integrated_ai_cache.get_text_tier_statistics() 
        op_perf = integrated_ai_cache.get_operation_performance()
        
        # Operation counts should be consistent
        summary_total = summary['total_operations']
        op_perf_total = sum(op['total_operations'] for op in op_perf['operations'].values())
        
        # Should be related (may not be exactly equal due to different counting methods)
        assert abs(summary_total - op_perf_total) <= summary_total * 0.1  # Within 10%
        
        # Tier distribution should be consistent
        summary_tiers = set(summary['text_tier_distribution'].keys())
        stats_tiers = set(tier_stats['tier_distribution'].keys())
        
        # Should have significant overlap
        overlap = len(summary_tiers.intersection(stats_tiers))
        total_unique = len(summary_tiers.union(stats_tiers))
        overlap_percentage = overlap / total_unique if total_unique > 0 else 1.0
        assert overlap_percentage >= 0.5  # At least 50% overlap

    def test_monitoring_performance_impact(self, integrated_ai_cache):
        """Test that monitoring methods have minimal performance impact."""
        import time
        
        # Measure time for all monitoring methods
        start_time = time.time()
        
        summary = integrated_ai_cache.get_ai_performance_summary()
        tier_stats = integrated_ai_cache.get_text_tier_statistics()
        op_perf = integrated_ai_cache.get_operation_performance()
        recommendations = integrated_ai_cache._generate_ai_optimization_recommendations()
        
        total_time = time.time() - start_time
        
        # Should complete quickly (under 100ms for reasonable dataset)
        assert total_time < 0.1, f"Monitoring methods took {total_time:.3f}s, should be under 0.1s"
        
        # Should return valid data
        assert len(summary) > 5
        assert len(tier_stats) > 3
        assert len(op_perf) > 1
        assert isinstance(recommendations, list)