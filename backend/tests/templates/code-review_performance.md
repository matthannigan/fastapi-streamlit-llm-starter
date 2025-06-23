# Performance Tests Review Template - [PERFORMANCE_AREA]

> **Instructions:** Replace `[PERFORMANCE_AREA]` with the actual performance area (e.g., "Cache Performance", "API Throughput", "Memory Usage"). 
> This template helps systematically review performance tests to ensure they meet our criteria.

## Review Criteria for Performance Tests

Performance tests should meet these criteria:
- ✅ **System characteristic measurement** - Measure timing, throughput, resource usage, not functional correctness
- ✅ **Quantitative metrics** - Produce measurable data (response times, requests/second, memory usage, etc.)
- ✅ **Load and stress testing** - Test system behavior under various load conditions
- ✅ **Performance regression detection** - Establish baselines and detect performance degradation
- ✅ **Resource utilization monitoring** - Track CPU, memory, I/O, and network usage patterns

## Files to Review

> **Instructions:** 
> 1. List all test files in the `backend/tests/performance/` directory
> 2. Group them by logical categories (examples below)
> 3. Include file sizes and line counts for context
> 4. Use checkboxes `[ ]` initially, then mark `[x]` when reviewed
> 5. Add status indicators: **✅ PROPER PERFORMANCE**, **❌ MOVE TO [DIRECTORY]**, **⚠️ PLACEHOLDER**

### Response Time & Latency Tests
- [ ] `test_[component]_latency.py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[api]_response_times.py` ([SIZE], [LINES] lines) - [Brief description]

### Throughput & Load Tests
- [ ] `test_[service]_throughput.py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[component]_load.py` ([SIZE], [LINES] lines) - [Brief description]

### Resource Usage Tests
- [ ] `test_[component]_memory.py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[service]_cpu_usage.py` ([SIZE], [LINES] lines) - [Brief description]

### Scalability & Stress Tests
- [ ] `test_[system]_scalability.py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[component]_stress.py` ([SIZE], [LINES] lines) - [Brief description]

### Benchmark & Regression Tests
- [ ] `test_[component]_benchmarks.py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[service]_performance_regression.py` ([SIZE], [LINES] lines) - [Brief description]

### Concurrency & Parallel Performance
- [ ] `test_[component]_concurrency.py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[service]_parallel_performance.py` ([SIZE], [LINES] lines) - [Brief description]

> **Note:** Adjust categories based on your performance testing structure. Common categories include:
> - Response Time & Latency, Throughput & Load, Resource Usage, Scalability & Stress, Benchmarks & Regression, Concurrency, etc.

## Review Notes

### Completed Reviews

> **Instructions:** For each file reviewed, add an entry like this:

**[N]. `test_[performance_area].py` [STATUS_ICON] [CLASSIFICATION]**
   - [Key findings about what the test measures]
   - [Assessment of quantitative metrics and benchmarks]
   - [Notes about load testing and stress conditions]
   - [Coverage of performance characteristics and regression detection]
   - Status: [Current location assessment and recommendation]

> **Status Icons:** ✅ ❌ ⚠️
> **Classifications:** 
> - **PROPER PERFORMANCE** - correctly located and designed performance tests
> - **MISPLACED - [TEST_TYPE]** - should be moved to different directory
> - **PLACEHOLDER FILE** - contains only placeholder tests

### Issues Found

> **Instructions:** List all issues discovered during review:

1. **[Issue category]** ([file names]) [description]
2. **[Issue category]** ([file names]) [description]

> **Common issue categories:**
> - Placeholder files, Misplaced functional tests, Misplaced integration tests, Missing quantitative metrics, Insufficient load testing, etc.

### Recommendations

#### Immediate Actions
1. **Move misplaced tests:**
   - Move `test_[file].py` → `tests/[correct_directory]/test_[new_name].py`

2. **Complete placeholder tests:**
   - Implement `test_[file].py` with actual performance measurement tests
   - Or remove if performance characteristics are covered elsewhere

3. **Fix performance test violations:**
   - [Specific recommendations for files that don't meet performance test criteria]

#### Overall Assessment

> **Instructions:** Provide overall assessment using this structure:

**[ASSESSMENT_LEVEL]** performance test compliance! [Brief summary]

- ✅/❌ **System characteristic measurement** - [Assessment details]
- ✅/❌ **Quantitative metrics collection** - [Assessment details]  
- ✅/❌ **Load and stress testing** - [Assessment details]
- ✅/❌ **Performance regression detection** - [Assessment details]
- ✅/❌ **Resource utilization monitoring** - [Assessment details]

**Key Strengths:**
- [List major strengths found in the performance tests]

**Areas for Improvement:**
- [List areas that need attention in performance testing]

> **Assessment levels:** EXCELLENT, GOOD, FAIR, NEEDS IMPROVEMENT

## Review Progress

> **Instructions:** Update these metrics as you progress:

**Started:** [DATE]
**Files Reviewed:** [X]/[TOTAL] ([PERCENTAGE]% complete)
**Issues Found:** [COUNT] ([breakdown by type])
**Recommendations Made:** [COUNT]

---

## Usage Instructions

### How to Use This Template

1. **Preparation:**
   - Copy this template to `backend/tests/performance/performance_review.md`
   - Replace `[PERFORMANCE_AREA]` with your actual performance area name
   - List all test files in the target directory

2. **File Discovery:**
   ```bash
   # Get file list with sizes
   ls -la backend/tests/performance/
   
   # Get line counts
   wc -l backend/tests/performance/*.py
   ```

3. **Review Process:**
   - Read each test file systematically
   - Check against performance test criteria
   - Look for quantitative measurements, timing, throughput, resource usage
   - Assess load testing scenarios and stress conditions
   - Note coverage gaps in performance characteristics

4. **Classification Guidelines:**
   - **✅ PROPER PERFORMANCE:** Measures system characteristics, timing, throughput, resource usage
   - **❌ MOVE TO INFRASTRUCTURE:** Tests component functionality without performance measurement
   - **❌ MOVE TO INTEGRATION:** Tests functional integration without performance focus
   - **❌ MOVE TO API:** Tests API functionality without performance measurement
   - **❌ MOVE TO SERVICES:** Tests business logic without performance focus
   - **⚠️ PLACEHOLDER:** Only contains TODO or empty tests

5. **Final Steps:**
   - Add TODO comments to misplaced files
   - Update progress tracking
   - Provide comprehensive recommendations

### Review Criteria Details

**System characteristic measurement:**
- Tests measure response times, latency, and processing speed
- Focus on quantifiable system behavior, not functional correctness
- Measure actual system performance under realistic conditions
- Track performance metrics over time

**Quantitative metrics:**
- Produce measurable data (milliseconds, requests/second, bytes/second)
- Establish performance baselines and thresholds
- Generate performance reports and statistics
- Use timing libraries and profiling tools

**Load and stress testing:**
- Test system behavior under various load conditions
- Simulate concurrent users and high traffic scenarios
- Test scalability limits and breaking points
- Measure degradation patterns under stress

**Performance regression detection:**
- Establish baseline performance measurements
- Compare current performance against historical data
- Detect performance degradation over time
- Alert on performance threshold violations

**Resource utilization monitoring:**
- Track CPU usage, memory consumption, and I/O patterns
- Monitor network bandwidth and connection usage
- Measure database query performance and connection pooling
- Track cache hit rates and storage efficiency 