# Resilience API Documentation

The Resilience API provides comprehensive endpoints for managing, configuring, and monitoring resilience infrastructure in your FastAPI application. This API enables you to configure circuit breakers, retry mechanisms, performance benchmarks, and advanced monitoring capabilities.

## 🏗️ **Architecture Overview**

The resilience API is organized into **8 focused modules** providing **38 endpoints** across two main categories:

### **Configuration Management** (`/resilience/config/*`)
- **config_validation.py** - Configuration validation and security checks
- **config_presets.py** - Environment-specific preset configurations  
- **config_templates.py** - Configuration blueprints and templates

### **Operations & Monitoring** (`/resilience/*`)
- **health.py** - Health monitoring and core metrics
- **circuit_breakers.py** - Circuit breaker management
- **monitoring.py** - Analytics and usage monitoring
- **performance.py** - Performance benchmarking and testing

## 🛡️ **Authentication**

All endpoints require API key authentication via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" \
     -X GET "http://localhost:8000/resilience/health"
```

## 📋 **Complete Endpoint Reference**

### **Configuration Validation** (`/resilience/config/*`)

#### **Basic Validation**
```http
POST /resilience/config/validate
```
Validate custom resilience configurations against standard requirements.

**Request:**
```json
{
  "configuration": {
    "retry_attempts": 3,
    "circuit_breaker_threshold": 5,
    "timeout_seconds": 30
  }
}
```

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["Consider adding exponential backoff"],
  "suggestions": ["Add strategy specification for completeness"]
}
```

#### **Security Validation**
```http
POST /resilience/config/validate-secure
```
Enhanced validation with security checks and metadata collection.

**Response includes additional security_info:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "suggestions": ["Consider timeout configuration"],
  "security_info": {
    "size_bytes": 128,
    "max_size_bytes": 4096,
    "field_count": 3,
    "validation_timestamp": "2023-12-01T10:30:00Z"
  }
}
```

#### **JSON String Validation**
```http
POST /resilience/config/validate-json
```
Validate configurations provided as JSON strings.

**Request:**
```json
{
  "json_config": "{\"retry_attempts\": 3, \"circuit_breaker_threshold\": 5}"
}
```

#### **Field Whitelist Validation**
```http
POST /resilience/config/validate/field-whitelist
```
Validate configurations against security field whitelist.

**Response:**
```json
{
  "is_valid": false,
  "errors": ["Field 'invalid_field' is not in the allowed whitelist"],
  "field_analysis": {
    "retry_attempts": {"allowed": true, "type": "int"},
    "invalid_field": {"allowed": false, "current_value": "not_allowed"}
  },
  "allowed_fields": ["retry_attempts", "circuit_breaker_threshold", "timeout_seconds"]
}
```

#### **Security Configuration Info**
```http
GET /resilience/config/validate/security-config
```
Get current security validation configuration and limits.

#### **Rate Limiting Status**
```http
GET /resilience/config/validate/rate-limit-status?client_ip=192.168.1.1
```
Check current rate limiting status for validation requests.

### **Configuration Presets** (`/resilience/config/*`)

#### **List All Presets**
```http
GET /resilience/config/presets
```
Get summary of all available environment-specific presets.

**Response:**
```json
[
  {
    "name": "production",
    "description": "High-reliability configuration for production",
    "retry_attempts": 3,
    "circuit_breaker_threshold": 5,
    "recovery_timeout": 60,
    "default_strategy": "conservative",
    "environment_contexts": ["prod", "production"]
  }
]
```

#### **Get Preset Details**
```http
GET /resilience/config/presets/{preset_name}
```
Get comprehensive details for a specific preset.

#### **Get All Presets Summary**
```http
GET /resilience/config/presets-summary
```
Get detailed information for all presets in a single response.

#### **Environment-Based Recommendation**
```http
GET /resilience/config/recommend-preset/{environment}
```
Get intelligent preset recommendation for a deployment environment.

**Example:**
```bash
GET /resilience/config/recommend-preset/production
```

**Response:**
```json
{
  "environment_detected": "production",
  "recommended_preset": "production",
  "confidence_score": 0.95,
  "reasoning": "High-reliability requirements detected for production environment",
  "alternative_presets": ["high_performance", "enterprise"],
  "environment_analysis": {
    "reliability_requirements": "high",
    "performance_needs": "moderate"
  }
}
```

#### **Auto-Detect Recommendation**
```http
GET /resilience/config/recommend-preset-auto
```
Automatically detect and recommend optimal preset based on current system state.

### **Configuration Templates** (`/resilience/config/*`)

#### **List All Templates**
```http
GET /resilience/config/templates
```
Get all available configuration templates with descriptions.

**Response:**
```json
{
  "templates": {
    "production": {
      "description": "High-reliability template for production",
      "use_cases": ["enterprise", "critical-systems"],
      "parameters": {
        "retry_attempts": {"type": "int", "range": [1, 10]},
        "circuit_breaker_threshold": {"type": "int", "range": [1, 20]}
      }
    }
  }
}
```

#### **Get Template Details**
```http
GET /resilience/config/templates/{template_name}
```
Get complete configuration details for a specific template.

#### **Validate Template-Based Configuration**
```http
POST /resilience/config/validate-template
```
Validate configuration using a template with optional overrides.

**Request:**
```json
{
  "template_name": "production",
  "overrides": {
    "retry_attempts": 5
  }
}
```

#### **Suggest Template for Configuration**
```http
POST /resilience/config/recommend-template
```
Analyze a configuration and suggest the most appropriate template.

**Request:**
```json
{
  "configuration": {
    "retry_attempts": 3,
    "circuit_breaker_threshold": 5,
    "default_strategy": "conservative"
  }
}
```

**Response:**
```json
{
  "suggested_template": "production",
  "confidence": 0.85,
  "reasoning": "Configuration closely matches 'production' template with 3/3 key parameters matching",
  "available_templates": ["production", "development", "testing"]
}
```

### **Health & Metrics** (`/resilience/*`)

#### **Core Health Check**
```http
GET /resilience/health
```
Get basic health status of the resilience service.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T10:30:00Z",
  "service": "resilience",
  "version": "1.0.0"
}
```

#### **Detailed Health Status**
```http
GET /resilience/health/detailed
```
Get comprehensive health information including circuit breaker states.

#### **Service Metrics**
```http
GET /resilience/metrics
```
Get detailed metrics for all resilience operations.

#### **Operation-Specific Metrics**
```http
GET /resilience/metrics/{operation_name}
```
Get metrics for a specific operation.

#### **Reset Metrics**
```http
POST /resilience/metrics/reset
```
Reset metrics for specific or all operations.

**Request:**
```json
{
  "operation_name": "text_processing",  // Optional: specific operation
  "confirm": true
}
```

#### **Configuration Monitoring**
```http
GET /resilience/config-monitoring
```
Get configuration monitoring and change tracking information.

### **Circuit Breakers** (`/resilience/*`)

#### **List Circuit Breakers**
```http
GET /resilience/circuit-breakers
```
Get status and configuration of all circuit breakers.

**Response:**
```json
{
  "circuit_breakers": {
    "text_processing": {
      "state": "closed",
      "failure_count": 2,
      "threshold": 5,
      "recovery_timeout": 60,
      "last_failure": "2023-12-01T10:25:00Z"
    }
  },
  "total_count": 1,
  "healthy_count": 1,
  "open_count": 0
}
```

#### **Get Circuit Breaker Details**
```http
GET /resilience/circuit-breakers/{breaker_name}
```
Get detailed information about a specific circuit breaker.

#### **Reset Circuit Breaker**
```http
POST /resilience/circuit-breakers/{breaker_name}/reset
```
Manually reset a circuit breaker to closed state.

**Response:**
```json
{
  "message": "Circuit breaker 'text_processing' has been reset to closed state",
  "breaker_name": "text_processing",
  "previous_state": "open",
  "new_state": "closed",
  "reset_timestamp": "2023-12-01T10:30:00Z"
}
```

### **Monitoring & Analytics** (`/resilience/*`)

#### **Usage Statistics**
```http
GET /resilience/usage-statistics
```
Get comprehensive usage statistics and trends.

#### **Preset Trends**
```http
GET /resilience/preset-trends/{preset_name}
```
Get usage trends for a specific preset.

#### **Performance Metrics**
```http
GET /resilience/performance-metrics
```
Get performance metrics and benchmarking data.

#### **Alerts**
```http
GET /resilience/alerts
```
Get current alerts and notifications.

#### **Session Information**
```http
GET /resilience/session/{session_id}
```
Get detailed information about a specific monitoring session.

#### **Export Data**
```http
GET /resilience/export
```
Export monitoring data in various formats.

#### **Cleanup Operations**
```http
POST /resilience/cleanup
```
Perform cleanup of old monitoring data.

### **Performance Benchmarking** (`/resilience/*`)

#### **Get Benchmark Data**
```http
GET /resilience/benchmark
```
Get current benchmark results and performance data.

#### **Run Performance Benchmark**
```http
POST /resilience/benchmark
```
Execute performance benchmark tests.

**Request:**
```json
{
  "operation_name": "text_processing",
  "iterations": 1000,
  "concurrency": 10
}
```

**Response:**
```json
{
  "benchmark_id": "bench_20231201_103000",
  "operation_name": "text_processing",
  "results": {
    "total_time": 45.2,
    "average_response_time": 0.045,
    "requests_per_second": 22.1,
    "success_rate": 0.998,
    "p95_response_time": 0.089
  },
  "timestamp": "2023-12-01T10:30:00Z"
}
```

#### **Performance Thresholds**
```http
GET /resilience/thresholds
```
Get current performance thresholds and limits.

#### **Performance Report**
```http
GET /resilience/report
```
Get comprehensive performance analysis report.

#### **Performance History**
```http
GET /resilience/history
```
Get historical performance data and trends.

## 🚀 **Usage Examples**

### **Basic Configuration Workflow**

1. **List available presets:**
```bash
curl -H "X-API-Key: your-key" \
     GET "http://localhost:8000/resilience/config/presets"
```

2. **Get preset details:**
```bash
curl -H "X-API-Key: your-key" \
     GET "http://localhost:8000/resilience/config/presets/production"
```

3. **Validate custom configuration:**
```bash
curl -H "X-API-Key: your-key" \
     -H "Content-Type: application/json" \
     -d '{"configuration": {"retry_attempts": 3}}' \
     POST "http://localhost:8000/resilience/config/validate"
```

### **Template-Based Configuration**

1. **List templates:**
```bash
curl -H "X-API-Key: your-key" \
     GET "http://localhost:8000/resilience/config/templates"
```

2. **Validate with template:**
```bash
curl -H "X-API-Key: your-key" \
     -H "Content-Type: application/json" \
     -d '{"template_name": "production", "overrides": {"retry_attempts": 5}}' \
     POST "http://localhost:8000/resilience/config/validate-template"
```

### **Monitoring Workflow**

1. **Check overall health:**
```bash
curl -H "X-API-Key: your-key" \
     GET "http://localhost:8000/resilience/health"
```

2. **Monitor circuit breakers:**
```bash
curl -H "X-API-Key: your-key" \
     GET "http://localhost:8000/resilience/circuit-breakers"
```

3. **Get performance metrics:**
```bash
curl -H "X-API-Key: your-key" \
     GET "http://localhost:8000/resilience/performance-metrics"
```

### **Performance Testing**

1. **Run benchmark:**
```bash
curl -H "X-API-Key: your-key" \
     -H "Content-Type: application/json" \
     -d '{"operation_name": "text_processing", "iterations": 100}' \
     POST "http://localhost:8000/resilience/benchmark"
```

2. **Check thresholds:**
```bash
curl -H "X-API-Key: your-key" \
     GET "http://localhost:8000/resilience/thresholds"
```

## 🔧 **Configuration Concepts**

### **Presets vs. Templates**

**Presets** are **environment-specific ready-to-use configurations**:
- Optimized for specific deployment environments (dev, test, prod)
- Complete configurations with all parameters set
- Environment-aware recommendations
- Use when: You want a proven configuration for your environment

**Templates** are **configuration blueprints for customization**:
- Flexible patterns that can be customized with overrides
- Structured starting points for custom configurations  
- Parameter validation and constraint checking
- Use when: You need a base configuration to customize

### **Validation Levels**

1. **Basic Validation** (`/validate`) - Schema and logic validation
2. **Security Validation** (`/validate-secure`) - Enhanced security checks
3. **Field Whitelist** (`/validate/field-whitelist`) - Security field filtering
4. **Template Validation** (`/validate-template`) - Template-based validation

## 📊 **Response Models**

### **ValidationResponse**
```json
{
  "is_valid": boolean,
  "errors": ["string"],
  "warnings": ["string"], 
  "suggestions": ["string"],
  "security_info": {
    "size_bytes": number,
    "max_size_bytes": number,
    "field_count": number,
    "validation_timestamp": "string"
  }
}
```

### **PresetSummary**
```json
{
  "name": "string",
  "description": "string", 
  "retry_attempts": number,
  "circuit_breaker_threshold": number,
  "recovery_timeout": number,
  "default_strategy": "string",
  "environment_contexts": ["string"]
}
```

### **BenchmarkResults**
```json
{
  "benchmark_id": "string",
  "operation_name": "string",
  "results": {
    "total_time": number,
    "average_response_time": number,
    "requests_per_second": number,
    "success_rate": number,
    "p95_response_time": number
  },
  "timestamp": "string"
}
```

## ⚡ **Rate Limiting**

- **Validation endpoints**: 60 requests/minute, 1000 requests/hour per IP
- **Monitoring endpoints**: Higher limits for operational needs
- **Benchmark endpoints**: Lower limits due to resource intensity

Check current status: `GET /resilience/config/validate/rate-limit-status`

## 🛠️ **Development & Testing**

### **Local Development**
```bash
# Start the backend
cd backend
uvicorn app.main:app --reload --port 8000

# Test endpoints
curl -H "X-API-Key: dev-test-key" \
     GET "http://localhost:8000/resilience/health"
```

### **Integration Testing**
The API provides comprehensive test endpoints and mock data for integration testing. Refer to the test files in `backend/tests/api/internal/resilience/` for examples.

## 📈 **Monitoring & Observability**

The resilience API provides built-in monitoring capabilities:

- **Health checks** for service status
- **Metrics collection** for performance analysis  
- **Circuit breaker monitoring** for failure detection
- **Usage analytics** for optimization insights
- **Performance benchmarking** for capacity planning

## 🔒 **Security Features**

- **API key authentication** on all endpoints
- **Rate limiting** to prevent abuse
- **Input validation** and sanitization
- **Security-focused validation** endpoints
- **Field whitelisting** for configuration security
- **Audit logging** for security monitoring
