---
sidebar_label: test_compression_middleware
---

# Comprehensive tests for Compression Middleware

  file_path: `backend/tests/core/middleware/test_compression_middleware.py`

Tests cover request decompression, response compression, algorithm selection,
content-type handling, and streaming compression features.

## TestCompressionMiddleware

Test the main compression middleware.

### settings()

```python
def settings(self):
```

Test settings with compression configuration.

### app()

```python
def app(self, settings):
```

FastAPI test app with compression middleware.

### test_middleware_initialization()

```python
def test_middleware_initialization(self, settings):
```

Test middleware initialization with different configurations.

### test_disabled_compression()

```python
def test_disabled_compression(self):
```

Test middleware when compression is disabled.

### test_response_compression_large_json()

```python
def test_response_compression_large_json(self, app):
```

Test response compression for large JSON responses.

### test_response_no_compression_small()

```python
def test_response_no_compression_small(self, app):
```

Test that small responses are not compressed.

### test_compression_algorithm_selection()

```python
def test_compression_algorithm_selection(self, app):
```

Test compression algorithm selection based on Accept-Encoding.

### test_compression_quality_values()

```python
def test_compression_quality_values(self, app):
```

Test compression algorithm selection with quality values.

### test_no_compression_unsupported_encoding()

```python
def test_no_compression_unsupported_encoding(self, app):
```

Test no compression when client doesn't support any algorithms.

### test_request_decompression_gzip()

```python
def test_request_decompression_gzip(self, app):
```

Test decompression of gzip-compressed request bodies.

### test_request_decompression_brotli()

```python
def test_request_decompression_brotli(self, app):
```

Test decompression of brotli-compressed request bodies.

### test_request_decompression_error()

```python
def test_request_decompression_error(self, app):
```

Test error handling for invalid compressed request data.

## TestCompressionAlgorithms

Test individual compression algorithms.

### middleware()

```python
def middleware(self):
```

Compression middleware instance for testing.

### test_gzip_compression()

```python
def test_gzip_compression(self, middleware):
```

Test gzip compression functionality.

### test_deflate_compression()

```python
def test_deflate_compression(self, middleware):
```

Test deflate compression functionality.

### test_brotli_compression()

```python
def test_brotli_compression(self, middleware):
```

Test brotli compression functionality.

### test_brotli_fallback_to_gzip()

```python
def test_brotli_fallback_to_gzip(self, middleware):
```

Test brotli fallback to gzip on compression error.

### test_gzip_decompression()

```python
def test_gzip_decompression(self, middleware):
```

Test gzip decompression functionality.

### test_brotli_decompression()

```python
def test_brotli_decompression(self, middleware):
```

Test brotli decompression functionality.

## TestCompressionDecisionLogic

Test compression decision logic.

### middleware()

```python
def middleware(self):
```

Compression middleware instance.

### test_should_compress_json_response()

```python
def test_should_compress_json_response(self, middleware):
```

Test compression decision for JSON responses.

### test_should_not_compress_small_response()

```python
def test_should_not_compress_small_response(self, middleware):
```

Test no compression for small responses.

### test_should_not_compress_already_compressed()

```python
def test_should_not_compress_already_compressed(self, middleware):
```

Test no compression for already compressed responses.

### test_should_not_compress_images()

```python
def test_should_not_compress_images(self, middleware):
```

Test no compression for image content.

### test_should_compress_text_content()

```python
def test_should_compress_text_content(self, middleware):
```

Test compression for text content types.

### test_should_not_compress_incompressible_types()

```python
def test_should_not_compress_incompressible_types(self, middleware):
```

Test no compression for incompressible content types.

## TestAcceptEncodingParsing

Test Accept-Encoding header parsing.

### middleware()

```python
def middleware(self):
```

Compression middleware instance.

### test_parse_simple_encoding()

```python
def test_parse_simple_encoding(self, middleware):
```

Test parsing simple Accept-Encoding header.

### test_parse_encoding_with_quality()

```python
def test_parse_encoding_with_quality(self, middleware):
```

Test parsing Accept-Encoding with quality values.

### test_parse_encoding_quality_ordering()

```python
def test_parse_encoding_quality_ordering(self, middleware):
```

Test that encodings are ordered by quality value.

### test_parse_encoding_zero_quality()

```python
def test_parse_encoding_zero_quality(self, middleware):
```

Test that encodings with q=0 are excluded.

### test_parse_empty_encoding()

```python
def test_parse_empty_encoding(self, middleware):
```

Test parsing empty Accept-Encoding header.

### test_parse_encoding_unsupported_algorithms()

```python
def test_parse_encoding_unsupported_algorithms(self, middleware):
```

Test that unsupported algorithms are filtered out.

## TestStreamingCompressionMiddleware

Test streaming compression middleware.

### settings()

```python
def settings(self):
```

Test settings.

### streaming_app()

```python
def streaming_app(self, settings):
```

App with streaming compression middleware.

### test_streaming_compression_initialization()

```python
async def test_streaming_compression_initialization(self, streaming_app, settings):
```

Test streaming middleware initialization.

### test_streaming_compression_non_http()

```python
async def test_streaming_compression_non_http(self, streaming_app):
```

Test streaming middleware with non-HTTP scope.

### test_streaming_compression_no_gzip_support()

```python
async def test_streaming_compression_no_gzip_support(self, streaming_app):
```

Test streaming middleware when client doesn't support gzip.

## TestCompressionUtilities

Test compression utility functions.

### test_get_compression_stats_compressed_response()

```python
def test_get_compression_stats_compressed_response(self):
```

Test compression statistics for compressed response.

### test_get_compression_stats_uncompressed_response()

```python
def test_get_compression_stats_uncompressed_response(self):
```

Test compression statistics for uncompressed response.

### test_configure_compression_settings_defaults()

```python
def test_configure_compression_settings_defaults(self):
```

Test compression settings configuration with defaults.

### test_configure_compression_settings_custom()

```python
def test_configure_compression_settings_custom(self):
```

Test compression settings with custom values.

### test_configure_compression_settings_validation()

```python
def test_configure_compression_settings_validation(self):
```

Test compression settings validation.

### test_configure_compression_settings_empty_algorithms()

```python
def test_configure_compression_settings_empty_algorithms(self):
```

Test compression settings with no valid algorithms.

## TestCompressionIntegration

Integration tests for compression middleware.

### full_compression_app()

```python
def full_compression_app(self):
```

App with full compression configuration.

### test_end_to_end_compression_flow()

```python
def test_end_to_end_compression_flow(self, full_compression_app):
```

Test complete compression flow from request to response.

### test_mixed_content_handling()

```python
def test_mixed_content_handling(self, full_compression_app):
```

Test handling of different content types.

### test_request_response_compression_cycle()

```python
def test_request_response_compression_cycle(self, full_compression_app):
```

Test both request decompression and response compression.

## TestCompressionPerformance

Performance tests for compression middleware.

### performance_app()

```python
def performance_app(self):
```

App configured for performance testing.

### test_compression_performance_overhead()

```python
def test_compression_performance_overhead(self, performance_app):
```

Test performance overhead of compression.

### test_compression_ratio_effectiveness()

```python
def test_compression_ratio_effectiveness(self, performance_app):
```

Test compression effectiveness and ratios.
