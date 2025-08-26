# Streamlit Frontend Agent Guidance

This file provides guidance to coding assistants and agents when working with code in the `frontend` subdirectory of this project.

General agent instructions regarding the repository overall are available at `../AGENTS.md`.

## Frontend Architecture

The Streamlit frontend demonstrates **production-ready patterns** for AI application development:

### Frontend Architecture Patterns Demonstrated
- **Modular Component Design**: Single-responsibility functions with clear separation of concerns
- **Configuration-Driven Behavior**: Environment-specific settings with Pydantic validation
- **Async API Communication**: Proper error handling and timeout management optimized for Streamlit
- **Dynamic UI Generation**: Interface adaptation based on backend capabilities
- **Session State Management**: Stateful user interactions with persistence
- **Progressive Disclosure**: Collapsible sections and smart defaults for better UX

### Production-Ready Frontend Features
**Modern Interface Design:**
- **Real-time Status Monitoring**: API health checks with visual indicators
- **Dynamic Operation Configuration**: Backend-driven UI generation
- **Intelligent Example System**: Operation-specific text recommendations
- **Multi-Modal Input Support**: Text entry and file upload with validation
- **Responsive Layout**: Adaptive design for different screen sizes
- **Progress Indicators**: Real-time feedback during processing
- **Results Persistence**: Session management with download functionality

**Error Handling & User Experience:**
- **Graceful Degradation**: Continues operation when backend is unavailable
- **Comprehensive Validation**: Input validation with clear error messages
- **Timeout Management**: Request timeout handling with user feedback
- **Accessibility Features**: Semantic markup and contextual help text

## Development Commands

The project includes a comprehensive `Makefile` for common tasks. Access the complete list of commands with `make help`. All Python scripts called from the `Makefile` run from the `.venv` virtual environment automatically.

**Issue**: `make: *** No rule to make target `help'.  Stop.`
**Solution**: The `Makefile` is located in the project root directory. You may be in a subdirectory. Verify current directory with `pwd`.

### Frontend Installation & Startup

```bash
# Recommended: Use Makefile commands (handles dependencies automatically)
make install-frontend-local   # Install frontend deps in current venv
make test-frontend            # Run frontend tests via Docker
make lint-frontend            # Run frontend code quality checks

# Manual commands (activate virtual environment first)
source .venv/bin/activate
cd frontend/

# Run Streamlit app with proper configuration
streamlit run app/app.py --server.port 8501

# For auto-reload during development
streamlit run app/app.py --server.runOnSave=true
```

#### Frontend Testing
The frontend includes comprehensive testing aligned with production standards:

```
frontend/tests/
├── test_api_client.py         # API communication tests with async patterns
├── test_config.py             # Configuration validation tests
├── conftest.py                # Shared test fixtures
└── pytest.ini                # Test configuration with parallel execution
```

**Test Features:**
- **Async Testing**: Proper async/await patterns for API communication
- **Mock Integration**: Isolated testing with httpx mocking
- **Parallel Execution**: Fast test execution with pytest-xdist
- **Coverage Reporting**: Comprehensive coverage analysis

## Frontend Configuration Management

**Environment-specific settings with Pydantic validation:**

### Development/Local Configuration
```bash
# Frontend Configuration
API_BASE_URL=http://localhost:8000
SHOW_DEBUG_INFO=true
INPUT_MAX_LENGTH=10000

# Health Check Configuration
HEALTH_CHECK_TIMEOUT_MS=2000
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=1000
HEALTH_CHECK_CACHE_TIMEOUT_MS=3000
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=1500
HEALTH_CHECK_RETRY_COUNT=1
```

### Production Configuration
```bash
# Frontend Configuration
API_BASE_URL=https://api.your-domain.com
SHOW_DEBUG_INFO=false
INPUT_MAX_LENGTH=50000

# Health Check Configuration  
HEALTH_CHECK_TIMEOUT_MS=2000
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=1000
HEALTH_CHECK_CACHE_TIMEOUT_MS=3000
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=1500
HEALTH_CHECK_RETRY_COUNT=2
```

## Customizing the Frontend

### UI Component Customization Patterns

**Key components to customize for your domain:**
- `display_results()` - Adapt result formatting for your data types
- `select_operation_sidebar()` - Update for your specific operations
- Operation-specific input forms - Customize for your business logic
- Example text suggestions - Replace with domain-relevant examples

**Production-Ready Patterns to Keep:**
- **Async API communication** - Maintain timeout and error handling
- **Configuration management** - Keep environment-based settings
- **Session state management** - Preserve user interaction patterns
- **Progressive disclosure** - Keep collapsible sections and smart defaults

### Frontend Architecture Guidelines

**When customizing the Streamlit frontend:**

1. **Keep architectural patterns** - async communication, error handling, configuration management
2. **Customize UI components** - adapt display and input components for your operations  
3. **Replace example content** - update AI operations and example texts for your domain
4. **Maintain test patterns** - keep async testing patterns and coverage standards

**Options for Frontend Development:**
- **Option 1**: Customize the existing Streamlit application with your operations and UI
- **Option 2**: Replace `frontend/` with your preferred UI technology (React, Vue, mobile app, etc.)
- **Either way**: Use the async API client patterns and error handling shown in the Streamlit implementation

## Frontend Testing Best Practices

**Async Testing Patterns:**
```python
# ✅ Test async API communication
@pytest.mark.asyncio
async def test_api_request_with_timeout():
    """Test that API client handles timeout properly."""
    async with httpx.AsyncClient() as client:
        # Test implementation with proper timeout handling
        pass
```

**Configuration Testing:**
```python
# ✅ Test configuration validation
def test_config_validation_for_required_fields():
    """Test that config validation catches missing required fields."""
    with pytest.raises(ValidationError):
        Config(api_base_url="")  # Missing required field
```

**Integration Testing with Backend:**
- Use the async patterns shown in `test_api_client.py`
- Mock external dependencies but test real integration paths
- Test error scenarios and graceful degradation

## See Also

- **Backend API Integration**: `../backend/AGENTS.md` for API endpoint details
- **Testing Methodology**: `../docs/guides/developer/TESTING.md` for comprehensive testing guidance
- **Configuration Management**: `../AGENTS.md` for environment variable patterns
- **Template Customization**: `../AGENTS.template-users.md` for customization guidance