---
sidebar_label: generate_api_key
---

# Generate secure API keys for the authentication system.

  file_path: `scripts/generate_api_key.py`

## generate_api_key()

```python
def generate_api_key(length: int = 32, prefix: str = 'sk') -> str:
```

Generate a cryptographically secure API key.

Args:
    length: Length of the random part (default: 32)
    prefix: Prefix for the key (default: "sk")
    
Returns:
    Generated API key

## generate_multiple_keys()

```python
def generate_multiple_keys(count: int, length: int = 32, prefix: str = 'sk') -> list:
```

Generate multiple API keys.

## main()

```python
def main():
```

Main function.
