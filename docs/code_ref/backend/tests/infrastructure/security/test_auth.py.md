---
sidebar_label: test_auth
---

# Unit tests for the authentication module.

  file_path: `backend/tests/infrastructure/security/test_auth.py`

## TestVerifyAPIKey

Test the verify_api_key dependency function.

### test_verify_api_key_with_valid_credentials()

```python
def test_verify_api_key_with_valid_credentials(self):
```

Test verify_api_key with valid credentials.

### test_verify_api_key_with_invalid_credentials()

```python
def test_verify_api_key_with_invalid_credentials(self):
```

Test verify_api_key with invalid credentials.

### test_verify_api_key_without_credentials()

```python
def test_verify_api_key_without_credentials(self):
```

Test verify_api_key without credentials.

### test_verify_api_key_development_mode_no_keys()

```python
def test_verify_api_key_development_mode_no_keys(self):
```

Test verify_api_key in development mode (no API keys configured).

### test_verify_api_key_test_mode_with_test_key()

```python
def test_verify_api_key_test_mode_with_test_key(self):
```

Test verify_api_key in test mode with test key.

### test_verify_api_key_test_mode_development_fallback()

```python
def test_verify_api_key_test_mode_development_fallback(self):
```

Test verify_api_key in test mode with development fallback.

### test_verify_api_key_empty_credentials()

```python
def test_verify_api_key_empty_credentials(self):
```

Test verify_api_key with empty credentials string.

## TestVerifyAPIKeyString

Test the verify_api_key_string utility function.

### test_verify_api_key_string_valid()

```python
def test_verify_api_key_string_valid(self):
```

Test verify_api_key_string with valid key.

### test_verify_api_key_string_invalid()

```python
def test_verify_api_key_string_invalid(self):
```

Test verify_api_key_string with invalid key.

### test_verify_api_key_string_empty()

```python
def test_verify_api_key_string_empty(self):
```

Test verify_api_key_string with empty key.

## TestOptionalVerifyAPIKey

Test the optional_verify_api_key dependency function.

### test_optional_verify_api_key_with_valid_credentials()

```python
def test_optional_verify_api_key_with_valid_credentials(self):
```

Test optional_verify_api_key with valid credentials.

### test_optional_verify_api_key_with_invalid_credentials()

```python
def test_optional_verify_api_key_with_invalid_credentials(self):
```

Test optional_verify_api_key with invalid credentials should raise exception.

### test_optional_verify_api_key_without_credentials()

```python
def test_optional_verify_api_key_without_credentials(self):
```

Test optional_verify_api_key without credentials should return None.

## TestVerifyAPIKeyWithMetadata

Test the verify_api_key_with_metadata dependency function.

### test_verify_api_key_with_metadata_valid_credentials()

```python
def test_verify_api_key_with_metadata_valid_credentials(self):
```

Test verify_api_key_with_metadata with valid credentials.

### test_verify_api_key_with_metadata_includes_metadata()

```python
def test_verify_api_key_with_metadata_includes_metadata(self):
```

Test verify_api_key_with_metadata includes metadata when enabled.

## TestAPIKeyAuth

Test the APIKeyAuth class.

### test_api_key_auth_verify_valid_key()

```python
def test_api_key_auth_verify_valid_key(self):
```

Test APIKeyAuth.verify_api_key with valid key.

### test_api_key_auth_verify_invalid_key()

```python
def test_api_key_auth_verify_invalid_key(self):
```

Test APIKeyAuth.verify_api_key with invalid key.

### test_api_key_auth_verify_empty_key()

```python
def test_api_key_auth_verify_empty_key(self):
```

Test APIKeyAuth.verify_api_key with empty key.

### test_api_key_auth_no_keys_configured()

```python
def test_api_key_auth_no_keys_configured(self):
```

Test APIKeyAuth with no keys configured.

### test_api_key_auth_case_sensitive()

```python
def test_api_key_auth_case_sensitive(self):
```

Test APIKeyAuth is case sensitive.

### test_api_key_auth_get_key_metadata()

```python
def test_api_key_auth_get_key_metadata(self):
```

Test APIKeyAuth.get_key_metadata functionality.

### test_api_key_auth_get_key_metadata_disabled()

```python
def test_api_key_auth_get_key_metadata_disabled(self):
```

Test APIKeyAuth.get_key_metadata when user tracking is disabled.

### test_api_key_auth_reload_keys()

```python
def test_api_key_auth_reload_keys(self):
```

Test APIKeyAuth.reload_keys functionality.

## TestAuthConfig

Test the AuthConfig class.

### test_auth_config_default_simple_mode()

```python
def test_auth_config_default_simple_mode(self):
```

Test AuthConfig defaults to simple mode.

### test_auth_config_advanced_mode()

```python
def test_auth_config_advanced_mode(self):
```

Test AuthConfig can be set to advanced mode.

### test_auth_config_feature_support_simple_mode()

```python
def test_auth_config_feature_support_simple_mode(self):
```

Test feature support in simple mode.

### test_auth_config_feature_support_advanced_mode()

```python
def test_auth_config_feature_support_advanced_mode(self):
```

Test feature support in advanced mode.

### test_auth_config_user_tracking_enabled()

```python
def test_auth_config_user_tracking_enabled(self):
```

Test user tracking can be enabled.

### test_auth_config_request_logging_enabled()

```python
def test_auth_config_request_logging_enabled(self):
```

Test request logging can be enabled.

### test_auth_config_get_auth_info()

```python
def test_auth_config_get_auth_info(self):
```

Test AuthConfig.get_auth_info returns proper structure.
