# API Authentication & Authorization

This document describes the authentication and authorization system implemented in the FastAPI application.

## Overview

The API uses **Bearer Token authentication** with API keys to protect sensitive endpoints. This provides a simple yet secure way to control access to the API.

## Features

- **Bearer Token Authentication**: Uses HTTP Authorization header with Bearer tokens
- **Multiple API Keys**: Support for primary and additional API keys
- **Development Mode**: Graceful fallback when no API keys are configured
- **Optional Authentication**: Some endpoints support optional authentication
- **Comprehensive Logging**: Authentication attempts and failures are logged
- **Runtime Key Reloading**: API keys can be reloaded without restarting the server

## Configuration

### Environment Variables

Add the following environment variables to configure authentication:

```bash
# Primary API key (required for production)
API_KEY=your_secure_api_key_here

# Additional API keys (optional, comma-separated)
ADDITIONAL_API_KEYS=key1,key2,key3
```

### Example Configuration

```bash
# Strong API key example
API_KEY=sk-1234567890abcdef1234567890abcdef12345678

# Multiple keys for different clients
ADDITIONAL_API_KEYS=client1-key-abc123,client2-key-def456,admin-key-xyz789
```

## API Key Security Best Practices

1. **Use Strong Keys**: Generate cryptographically secure random strings
2. **Minimum Length**: Use at least 32 characters
3. **Unique Keys**: Each client should have a unique API key
4. **Regular Rotation**: Rotate keys periodically
5. **Secure Storage**: Store keys in environment variables or secret managers
6. **Never Commit**: Never commit API keys to version control

### Generating Secure API Keys

```bash
# Using openssl
openssl rand -hex 32

# Using Python
python -c "import secrets; print('sk-' + secrets.token_hex(32))"

# Using Node.js
node -e "console.log('sk-' + require('crypto').randomBytes(32).toString('hex'))"
```

## Endpoint Protection Levels

### Public Endpoints (No Authentication Required)
- `GET /` - Root endpoint
- `GET /health` - Health check

### Protected Endpoints (Authentication Required)
- `POST /process` - Text processing (main API functionality)
- `GET /auth/status` - Authentication status check

### Optional Authentication Endpoints
- `GET /operations` - Available operations (works with or without auth)

## Usage Examples

### Making Authenticated Requests

#### Using curl
```bash
# Set your API key
export API_KEY="your_api_key_here"

# Make authenticated request
curl -X POST "http://localhost:8000/process" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "operation": "summarize"
  }'
```

#### Using Python requests
```python
import requests

api_key = "your_api_key_here"
headers = {"Authorization": f"Bearer {api_key}"}

response = requests.post(
    "http://localhost:8000/process",
    headers=headers,
    json={
        "text": "Hello world",
        "operation": "summarize"
    }
)
```

#### Using JavaScript fetch
```javascript
const apiKey = "your_api_key_here";

const response = await fetch("http://localhost:8000/process", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${apiKey}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    text: "Hello world",
    operation: "summarize"
  })
});
```

## Error Responses

### 401 Unauthorized - Missing API Key
```json
{
  "detail": "API key required. Please provide a valid API key in the Authorization header."
}
```

### 401 Unauthorized - Invalid API Key
```json
{
  "detail": "Invalid API key"
}
```

## Development Mode

When no API keys are configured (empty `API_KEY` and `ADDITIONAL_API_KEYS`), the system operates in development mode:

- All endpoints are accessible without authentication
- Warning messages are logged
- Useful for local development and testing

## Testing Authentication

Use the provided test script to verify authentication:

```bash
# 1. Start the server
cd backend
python -m uvicorn app.main:app --reload

# 2. Set API key
export API_KEY=test-api-key-12345

# 3. Run tests
python test_auth.py
```

## Monitoring and Logging

The authentication system provides comprehensive logging:

- **INFO**: Number of API keys loaded at startup
- **WARNING**: Unauthenticated access attempts, invalid keys
- **DEBUG**: Successful authentication events

Example log entries:
```
INFO - Loaded 3 API key(s)
WARNING - Invalid API key attempted: 12345678...
DEBUG - API key authentication successful
```

## Integration with Frontend

### Streamlit Integration

For the Streamlit frontend, you can store the API key in Streamlit secrets:

```toml
# .streamlit/secrets.toml
[api]
key = "your_api_key_here"
```

```python
# In your Streamlit app
import streamlit as st

api_key = st.secrets["api"]["key"]
headers = {"Authorization": f"Bearer {api_key}"}
```

## Production Deployment

### Docker Environment Variables

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - API_KEY=${API_KEY}
      - ADDITIONAL_API_KEYS=${ADDITIONAL_API_KEYS}
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
type: Opaque
stringData:
  API_KEY: "your_secure_api_key_here"
  ADDITIONAL_API_KEYS: "key1,key2,key3"
```

## Advanced Features

### Runtime Key Reloading

```python
from app.auth import api_key_auth

# Reload API keys without restarting
api_key_auth.reload_keys()
```

### Manual Key Verification

```python
from app.auth import verify_api_key_string

# Verify a key programmatically
is_valid = verify_api_key_string("some_api_key")
```

## Troubleshooting

### Common Issues

1. **403 Forbidden**: Check if API key is set in environment
2. **401 Unauthorized**: Verify API key format and value
3. **Missing Authorization Header**: Ensure Bearer token format

### Debug Steps

1. Check environment variables: `echo $API_KEY`
2. Verify server logs for authentication messages
3. Test with the provided test script
4. Use `/auth/status` endpoint to verify authentication

## Future Enhancements

Potential improvements for production systems:

1. **JWT Tokens**: Replace API keys with JWT for stateless auth
2. **Rate Limiting**: Add per-key rate limiting
3. **Key Expiration**: Implement key expiration dates
4. **Audit Logging**: Enhanced logging for compliance
5. **Role-Based Access**: Different permission levels
6. **OAuth2 Integration**: Support for OAuth2 flows 

See implementation details and recommendations in [ADVANCED_AUTH_GUIDE.md](./ADVANCED_AUTH_GUIDE.md).
