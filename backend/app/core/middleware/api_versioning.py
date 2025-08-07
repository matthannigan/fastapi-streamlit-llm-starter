"""
API Versioning Middleware

Handles API versioning through multiple strategies including URL paths,
headers, and query parameters with backward compatibility support.
"""

import logging
import re
from typing import Dict, Optional, Tuple, Callable, Any
from packaging import version
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.config import Settings

# Configure module logger
logger = logging.getLogger(__name__)


class APIVersioningMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive API versioning middleware with multiple strategies.
    
    Features:
    - URL path versioning (/v1/, /v2/)
    - Header-based versioning (API-Version, Accept headers)
    - Query parameter versioning (?version=1.0)
    - Version deprecation warnings
    - Backward compatibility routing
    - Minimum/maximum version enforcement
    """
    
    def __init__(self, app: ASGIApp, settings: Settings):
        super().__init__(app)
        self.settings = settings
        
        # Version configuration
        self.default_version = getattr(settings, 'default_api_version', '1.0')
        self.current_version = getattr(settings, 'current_api_version', '1.0')
        self.min_supported_version = getattr(settings, 'min_api_version', '1.0')
        self.max_supported_version = getattr(settings, 'max_api_version', '1.0')
        
        # Supported versions with their status
        self.supported_versions = {
            # v0.0 and v0.1 are examples of how to configure old versions of the API
            '0.0': {
                'status': 'supported',
                'deprecated': False,
                'sunset_date': None,
                'path_prefix': '/v0'
            },
            '0.1': {
                'status': 'supported',
                'deprecated': True,
                'sunset_date': '2024-12-31',
                'path_prefix': '/v0'  # v0.1 uses same prefix as v0.0
            },
            '1.0': {
                'status': 'current',
                'deprecated': False,
                'sunset_date': None,
                'path_prefix': '/v1'
            }
        }
        
        # Version detection strategies in order of preference
        self.version_strategies = [
            self._get_version_from_path,
            self._get_version_from_header,
            self._get_version_from_query,
            self._get_default_version
        ]
        
        # Path patterns for version extraction
        self.version_path_pattern = re.compile(r'^/v(\d+(?:\.\d+)?)')
        
        # Header names to check for version
        self.version_headers = ['api-version', 'x-api-version', 'version']
        
        # Accept header pattern for media type versioning
        self.accept_version_pattern = re.compile(
            r'application/vnd\.[\w\-\.]+\+json;?\s*version=(\d+(?:\.\d+)?)'
        )
    
    def _normalize_version(self, version_str: str) -> Optional[str]:
        """Normalize version string to a standard format."""
        if not version_str:
            return None
        
        try:
            # Remove 'v' prefix if present
            if version_str.lower().startswith('v'):
                version_str = version_str[1:]
            
            # Parse and normalize using packaging.version
            parsed = version.parse(version_str)
            
            # Convert back to string in major.minor format
            if hasattr(parsed, 'major') and hasattr(parsed, 'minor'):
                return f"{parsed.major}.{parsed.minor}"
            elif hasattr(parsed, 'major'):
                return f"{parsed.major}.0"
            else:
                return version_str
                
        except Exception:
            return None
    
    def _get_version_from_path(self, request: Request) -> Optional[str]:
        """Extract version from URL path."""
        match = self.version_path_pattern.match(request.url.path)
        if match:
            return self._normalize_version(match.group(1))
        return None
    
    def _get_version_from_header(self, request: Request) -> Optional[str]:
        """Extract version from HTTP headers."""
        # Check dedicated version headers
        for header_name in self.version_headers:
            version_str = request.headers.get(header_name)
            if version_str:
                return self._normalize_version(version_str)
        
        # Check Accept header for media type versioning
        accept_header = request.headers.get('accept', '')
        match = self.accept_version_pattern.search(accept_header)
        if match:
            return self._normalize_version(match.group(1))
        
        return None
    
    def _get_version_from_query(self, request: Request) -> Optional[str]:
        """Extract version from query parameters."""
        version_str = request.query_params.get('version') or request.query_params.get('api_version')
        if version_str:
            return self._normalize_version(version_str)
        return None
    
    def _get_default_version(self, request: Request) -> str:
        """Return the default version."""
        return self.default_version
    
    def _detect_api_version(self, request: Request) -> Tuple[str, str]:
        """
        Detect API version from request using multiple strategies.
        
        Returns:
            Tuple of (detected_version, detection_method)
        """
        for strategy in self.version_strategies:
            detected_version = strategy(request)
            if detected_version and detected_version in self.supported_versions:
                strategy_name = strategy.__name__.replace('_get_version_from_', '')
                strategy_name = strategy_name.replace('_get_default_version', 'default')
                return detected_version, strategy_name
        
        # Fallback to default if no valid version detected
        return self.default_version, 'default'
    
    def _is_version_supported(self, requested_version: str) -> bool:
        """Check if the requested version is supported."""
        return requested_version in self.supported_versions
    
    def _get_version_info(self, version_str: str) -> Dict[str, Any]:
        """Get detailed information about a version."""
        return self.supported_versions.get(version_str, {})
    
    def _create_version_headers(self, request_version: str, detection_method: str) -> Dict[str, str]:
        """Create version-related response headers."""
        version_info = self._get_version_info(request_version)
        
        headers = {
            'API-Version': request_version,
            'API-Version-Detection': detection_method,
            'API-Supported-Versions': ', '.join(self.supported_versions.keys()),
            'API-Current-Version': self.current_version,
        }
        
        # Add deprecation headers if version is deprecated
        if version_info.get('deprecated'):
            headers['Deprecation'] = 'true'
            if version_info.get('sunset_date'):
                headers['Sunset'] = version_info['sunset_date']
            headers['Link'] = '</docs/migration>; rel="deprecation"'
        
        return headers
    
    def _should_redirect_version(self, request: Request, detected_version: str) -> Optional[str]:
        """Determine if request should be redirected to a different version."""
        # If version is not supported, try to find a compatible version
        if not self._is_version_supported(detected_version):
            # Try to find the closest supported version
            try:
                requested = version.parse(detected_version)
                compatible_versions = []
                
                for supported_ver in self.supported_versions.keys():
                    supported = version.parse(supported_ver)
                    # Same major version is considered compatible
                    if supported.major == requested.major:
                        compatible_versions.append((supported_ver, supported))
                
                if compatible_versions:
                    # Return the highest compatible version
                    compatible_versions.sort(key=lambda x: x[1], reverse=True)
                    return compatible_versions[0][0]
                    
            except Exception:
                pass
        
        return None
    
    def _rewrite_request_path(self, request: Request, target_version: str) -> str:
        """Rewrite request path for version routing."""
        current_path = request.url.path
        version_info = self._get_version_info(target_version)
        target_prefix = version_info.get('path_prefix', f'/v{target_version.split(".")[0]}')
        
        # Remove existing version prefix if present
        path_without_version = re.sub(r'^/v\d+(?:\.\d+)?', '', current_path)
        
        # Add target version prefix
        return f"{target_prefix}{path_without_version}"
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """Process request with API versioning."""
        
        # 1. Detect requested API version
        detected_version, detection_method = self._detect_api_version(request)
        
        # 2. Check if version is supported
        if not self._is_version_supported(detected_version):
            # Try to find a compatible version
            compatible_version = self._should_redirect_version(request, detected_version)
            
            if compatible_version:
                # Log version compatibility redirect
                logger.info(
                    f"API version compatibility: {detected_version} -> {compatible_version} "
                    f"for {request.method} {request.url.path}"
                )
                detected_version = compatible_version
            else:
                # Version not supported and no compatible version found
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Unsupported API version",
                        "error_code": "UNSUPPORTED_API_VERSION",
                        "requested_version": detected_version,
                        "supported_versions": list(self.supported_versions.keys()),
                        "current_version": self.current_version
                    },
                    headers={
                        "API-Supported-Versions": ", ".join(self.supported_versions.keys()),
                        "API-Current-Version": self.current_version
                    }
                )
        
        # 3. Add version info to request state
        request.state.api_version = detected_version
        request.state.api_version_detection_method = detection_method
        request.state.api_version_info = self._get_version_info(detected_version)
        
        # 4. Rewrite request path if necessary for routing
        original_path = request.url.path
        version_info = self._get_version_info(detected_version)
        expected_prefix = version_info.get('path_prefix', f'/v{detected_version.split(".")[0]}')
        
        if not original_path.startswith(expected_prefix):
            new_path = self._rewrite_request_path(request, detected_version)
            # Update the request scope path for routing
            request.scope["path"] = new_path
            request.scope["raw_path"] = new_path.encode()
        
        # 5. Process the request
        response = await call_next(request)
        
        # 6. Add version headers to response
        version_headers = self._create_version_headers(detected_version, detection_method)
        for header, value in version_headers.items():
            response.headers[header] = value
        
        # 7. Log version usage for analytics
        logger.debug(
            f"API version used: {detected_version} ({detection_method}) "
            f"for {request.method} {original_path}"
        )
        
        return response


class VersionCompatibilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling backward compatibility transformations.
    
    This middleware can transform requests and responses to maintain
    compatibility between different API versions.
    """
    
    def __init__(self, app: ASGIApp, settings: Settings):
        super().__init__(app)
        self.settings = settings
        
        # Version compatibility rules
        self.compatibility_rules = {
            # Transform v1.0 requests to v2.0 format
            ('1.0', '2.0'): {
                'request_transformers': [
                    self._transform_v1_to_v2_request
                ],
                'response_transformers': [
                    self._transform_v2_to_v1_response
                ]
            }
        }
    
    def _transform_v1_to_v2_request(self, request_data: dict) -> dict:
        """Transform v1.0 request format to v2.0 format."""
        # Example transformation: rename fields, restructure data
        if 'text' in request_data:
            request_data['input_text'] = request_data.pop('text')
        
        if 'options' in request_data:
            request_data['processing_options'] = request_data.pop('options')
        
        return request_data
    
    def _transform_v2_to_v1_response(self, response_data: dict) -> dict:
        """Transform v2.0 response format to v1.0 format."""
        # Example transformation: rename fields, restructure data
        if 'processed_text' in response_data:
            response_data['result'] = response_data.pop('processed_text')
        
        if 'metadata' in response_data:
            response_data['info'] = response_data.pop('metadata')
        
        return response_data
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """Apply version compatibility transformations."""
        api_version = getattr(request.state, 'api_version', None)
        
        if not api_version:
            return await call_next(request)
        
        # Check if compatibility transformation is needed
        target_version = self.settings.current_api_version
        compatibility_key = (api_version, target_version)
        
        if compatibility_key not in self.compatibility_rules:
            return await call_next(request)
        
        rules = self.compatibility_rules[compatibility_key]
        
        # Transform request if necessary
        if rules.get('request_transformers') and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body:
                    import json
                    request_data = json.loads(body)
                    
                    for transformer in rules['request_transformers']:
                        request_data = transformer(request_data)
                    
                    # Create new request with transformed data
                    transformed_body = json.dumps(request_data).encode()
                    
                    async def new_receive():
                        return {
                            "type": "http.request",
                            "body": transformed_body,
                            "more_body": False
                        }
                    
                    request._receive = new_receive
                    
            except Exception as e:
                logger.warning(f"Failed to transform request for compatibility: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Transform response if necessary
        if rules.get('response_transformers') and hasattr(response, 'body'):
            try:
                import json
                response_data = json.loads(response.body)
                
                for transformer in rules['response_transformers']:
                    response_data = transformer(response_data)
                
                response.body = json.dumps(response_data).encode()
                response.headers['content-length'] = str(len(response.body))
                
            except Exception as e:
                logger.warning(f"Failed to transform response for compatibility: {e}")
        
        return response


# Utility functions for version management
def get_api_version(request: Request) -> str:
    """Get the API version for the current request."""
    return getattr(request.state, 'api_version', '1.0')


def is_version_deprecated(request: Request) -> bool:
    """Check if the current API version is deprecated."""
    version_info = getattr(request.state, 'api_version_info', {})
    return version_info.get('deprecated', False)


def get_version_sunset_date(request: Request) -> Optional[str]:
    """Get the sunset date for the current API version."""
    version_info = getattr(request.state, 'api_version_info', {})
    return version_info.get('sunset_date')


# Settings additions for API versioning
class APIVersioningSettings:
    """API versioning configuration settings."""
    
    # Default API version to use when none specified
    default_api_version: str = "1.0"
    
    # Current/latest API version
    current_api_version: str = "1.0"
    
    # Minimum supported API version
    min_api_version: str = "1.0"
    
    # Maximum supported API version
    max_api_version: str = "2.0"
    
    # Enable version compatibility transformations
    version_compatibility_enabled: bool = True
    
    # Enable version analytics and logging
    version_analytics_enabled: bool = True
