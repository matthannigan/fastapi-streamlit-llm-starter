# Infrastructure Examples

This directory contains comprehensive examples demonstrating advanced usage of the infrastructure services available in the FastAPI Streamlit LLM Starter project. These examples serve as both learning materials and practical implementation guides.

## 📋 Available Examples

### 1. Advanced Infrastructure Demo (`advanced_infrastructure_demo.py`)

**Purpose:** Comprehensive demonstration showcasing how multiple infrastructure components work together in a production-like scenario.

**What it demonstrates:**
- 🏗️ **Complete Infrastructure Setup**: Shows how to initialize and configure all major infrastructure components
- 💾 **Advanced Caching Patterns**: AIResponseCache with custom configurations, tiered caching, and performance monitoring
- 🛡️ **Resilience Systems**: Circuit breakers, retry mechanisms, and different resilience strategies
- 🤖 **AI Infrastructure**: Secure prompt building, input sanitization, and response validation
- 📊 **Performance Monitoring**: Comprehensive metrics collection and analysis
- 🔐 **Security Integration**: Authentication, input validation, and secure processing workflows
- 🔄 **Integrated Workflows**: End-to-end processing pipelines combining all components

**Key Features:**
- Real-world scenarios with simulated AI service calls
- Error handling and graceful degradation patterns
- Performance optimization techniques
- Security best practices implementation

**Usage:**
```bash
cd backend
python -m app.examples.advanced_infrastructure_demo
```

### 2. Cache Configuration Examples (`cache_configuration_examples.py`)

**Purpose:** Focused examples demonstrating different AIResponseCache configuration patterns for various environments and use cases.

**What it demonstrates:**
- 🔧 **Basic Cache Setup**: Simple configuration for getting started
- 🛠️ **Development Configuration**: Optimized for fast development cycles
- 🚀 **Production Configuration**: High-performance settings with advanced monitoring
- 💾 **Memory-Only Fallback**: Graceful degradation when Redis is unavailable  
- 🗑️ **Cache Invalidation Patterns**: Different approaches to cache management
- 📊 **Performance Monitoring**: Using metrics to optimize cache performance

**Configuration Examples:**
- **Development**: Fast compression, short TTLs, smaller thresholds
- **Production**: Maximum compression, longer TTLs, comprehensive monitoring
- **Fallback**: InMemoryCache for Redis-less environments

**Usage:**
```bash
cd backend
python -m app.examples.cache_configuration_examples
```

## 🚀 Getting Started

### Prerequisites

1. **Python Environment**: Ensure you have Python 3.8+ with the project dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```

2. **Redis (Optional)**: While Redis provides the best experience, all examples gracefully degrade to memory-only operation if Redis is unavailable:
   ```bash
   # Start Redis locally (optional)
   docker run -d -p 6379:6379 redis:alpine
   ```

3. **Environment Variables**: Some examples may use environment variables for configuration:
   ```bash
   # Optional: Set in your .env file
   INPUT_MAX_LENGTH=2048
   AUTH_MODE=simple
   ```

### Running Examples

Each example is self-contained and can be run independently:

```bash
# Run from the backend directory
cd backend

# Advanced infrastructure demo
python -m app.examples.advanced_infrastructure_demo

# Cache configuration examples  
python -m app.examples.cache_configuration_examples
```

## 🏗️ Infrastructure Components Covered

### Cache Infrastructure
- **AIResponseCache**: Redis-based caching with compression and tiered storage
- **InMemoryCache**: High-performance in-memory caching with TTL and LRU eviction
- **CachePerformanceMonitor**: Comprehensive performance monitoring and analytics
- **Cache Key Generation**: Optimized key generation for large texts

### Resilience Infrastructure  
- **Circuit Breaker Pattern**: Automatic failure detection and service protection
- **Retry Mechanisms**: Intelligent retry with exponential backoff and jitter
- **Resilience Strategies**: Predefined strategies (aggressive, balanced, conservative, critical)
- **Orchestration**: Unified resilience patterns with decorators

### AI Infrastructure
- **Prompt Building**: Secure prompt construction with templates
- **Input Sanitization**: Comprehensive protection against prompt injection
- **Response Validation**: AI response validation and security checking
- **Template System**: Predefined templates for common AI operations

### Security Infrastructure
- **API Key Authentication**: Configurable authentication with multiple modes
- **Input Validation**: Multi-layer input sanitization and validation
- **Security Monitoring**: Request boundary logging and security metrics

### Monitoring & Metrics
- **Performance Tracking**: Real-time performance metrics collection
- **Memory Usage Monitoring**: Memory usage tracking with threshold alerting
- **Health Checks**: System health monitoring and status reporting
- **Metrics Export**: Compatible with monitoring systems

## 🎯 Learning Objectives

After reviewing these examples, you should understand:

1. **Component Integration**: How different infrastructure components work together
2. **Configuration Patterns**: How to configure components for different environments
3. **Performance Optimization**: How to use monitoring to optimize performance
4. **Error Handling**: How to implement robust error handling and graceful degradation
5. **Security Best Practices**: How to implement secure AI service operations
6. **Production Readiness**: How to prepare infrastructure for production deployment

## 🔧 Customization

These examples are designed to be easily customizable for your specific needs:

1. **Configuration Values**: Adjust TTLs, thresholds, and sizing based on your requirements
2. **Monitoring Thresholds**: Modify alerting thresholds based on your SLAs
3. **Resilience Strategies**: Create custom resilience configurations
4. **Security Policies**: Adapt security settings for your environment
5. **Cache Strategies**: Modify caching strategies based on your data patterns

## 📚 Additional Resources

For more information about the infrastructure components:

- 📖 [Cache Documentation](../infrastructure/cache/README.md)
- 🛡️ [Resilience Documentation](../infrastructure/resilience/README.md)  
- 🤖 [AI Infrastructure Documentation](../infrastructure/ai/)
- 🔐 [Security Documentation](../infrastructure/security/)
- 📊 [Monitoring Documentation](../infrastructure/monitoring/)

## 🐛 Troubleshooting

Common issues and solutions:

### Redis Connection Issues
```
⚠️ Redis connection failed: [Error] - caching disabled
```
**Solution**: Examples gracefully degrade to memory-only operation. Redis is optional for learning.

### Import Errors
```
ModuleNotFoundError: No module named 'app.infrastructure'
```
**Solution**: Run examples from the `backend` directory using the module syntax:
```bash
cd backend
python -m app.examples.advanced_infrastructure_demo
```

### Permission Errors
```
PermissionError: [Error] access denied
```
**Solution**: Ensure you have proper permissions and are running from the correct directory.

## 🤝 Contributing

When adding new examples:

1. Follow the existing patterns and naming conventions
2. Include comprehensive documentation and comments
3. Demonstrate real-world usage scenarios
4. Handle errors gracefully with informative logging
5. Update this README with your new example

---

**Note**: These examples are safe to run in any environment as they use mock data and don't modify persistent application data. They're designed for learning and experimentation.