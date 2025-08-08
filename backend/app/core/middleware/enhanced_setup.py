"""
Enhanced Middleware Setup Integration

Updated setup_middleware function to include all new middleware components
with proper configuration and ordering.
"""

def setup_enhanced_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Configure enhanced middleware stack with all available components.
    
    Enhanced Middleware Stack Order:
    1. **Rate Limiting Middleware**: Protect against abuse early
    2. **Request Size Limiting**: Prevent large request DoS attacks  
    3. **Security Middleware**: Security headers and validation
    4. **API Versioning Middleware**: Handle version detection and routing
    5. **Version Compatibility Middleware**: Transform between versions
    6. **Compression Middleware**: Handle request/response compression
    7. **Request Logging Middleware**: Log requests with correlation IDs
    8. **Performance Monitoring**: Track performance metrics
    9. **Application Logic**: Your route handlers
    10. **CORS Middleware**: Handle cross-origin responses
    11. **Global Exception Handler**: Catch any unhandled exceptions
    
    Args:
        app (FastAPI): The FastAPI application instance
        settings (Settings): Application settings with middleware configuration
    """
    logger.info("Setting up enhanced middleware stack")
    
    # 1. Rate Limiting Middleware (protect against abuse first)
    rate_limiting_enabled = getattr(settings, 'rate_limiting_enabled', True)
    if rate_limiting_enabled:
        app.add_middleware(RateLimitMiddleware, settings=settings)
        logger.info("Rate limiting middleware enabled")
    
    # 2. Request Size Limiting Middleware (prevent large request attacks)
    request_size_limiting_enabled = getattr(settings, 'request_size_limiting_enabled', True)
    if request_size_limiting_enabled:
        app.add_middleware(RequestSizeLimitMiddleware, settings=settings)
        logger.info("Request size limiting middleware enabled")
    
    # 3. Security Middleware (security headers and validation)
    security_enabled = getattr(settings, 'security_headers_enabled', True)
    if security_enabled:
        app.add_middleware(SecurityMiddleware, settings=settings)
        logger.info("Security middleware enabled")
    
    # 4. API Versioning Middleware (handle version detection)
    versioning_enabled = getattr(settings, 'api_versioning_enabled', True)
    if versioning_enabled:
        app.add_middleware(APIVersioningMiddleware, settings=settings)
        logger.info("API versioning middleware enabled")
    
    # 5. Version Compatibility Middleware (transform between versions)
    compatibility_enabled = getattr(settings, 'version_compatibility_enabled', False)
    if compatibility_enabled:
        app.add_middleware(VersionCompatibilityMiddleware, settings=settings)
        logger.info("Version compatibility middleware enabled")
    
    # 6. Compression Middleware (handle compression early for efficiency)
    compression_enabled = getattr(settings, 'compression_enabled', True)
    if compression_enabled:
        app.add_middleware(CompressionMiddleware, settings=settings)
        logger.info("Compression middleware enabled")
    
    # 7. Request Logging Middleware (log with all context available)
    request_logging_enabled = getattr(settings, 'request_logging_enabled', True)
    if request_logging_enabled:
        app.add_middleware(RequestLoggingMiddleware, settings=settings)
        logger.info("Request logging middleware enabled")
    
    # 8. Performance Monitoring Middleware (track performance)
    performance_monitoring_enabled = getattr(settings, 'performance_monitoring_enabled', True)
    if performance_monitoring_enabled:
        app.add_middleware(PerformanceMonitoringMiddleware, settings=settings)
        logger.info("Performance monitoring middleware enabled")
    
    # 9. Global Exception Handler (handle exceptions from all middleware)
    setup_global_exception_handler(app, settings)
    logger.info("Global exception handler configured")
    
    # 10. CORS Middleware (handle responses last)
    setup_cors_middleware(app, settings)
    logger.info("CORS middleware configured")
    
    logger.info("Enhanced middleware stack setup complete")


# Enhanced settings class additions
class EnhancedMiddlewareSettings:
    """
    Enhanced middleware configuration settings.
    
    This class extends the base Settings with configuration options
    for all the enhanced middleware components.
    """
    
    # === Rate Limiting Settings ===
    rate_limiting_enabled: bool = True
    rate_limiting_skip_health: bool = True
    redis_url: Optional[str] = None
    custom_rate_limits: Dict[str, Dict[str, int]] = {}
    custom_endpoint_rules: Dict[str, str] = {}
    
    # === Request Size Limiting Settings ===
    request_size_limiting_enabled: bool = True
    request_size_limits: Dict[str, int] = {
        'default': 10 * 1024 * 1024,  # 10MB
        'application/json': 5 * 1024 * 1024,  # 5MB
        'multipart/form-data': 50 * 1024 * 1024,  # 50MB
    }
    
    # === Compression Settings ===
    compression_enabled: bool = True
    compression_min_size: int = 1024  # 1KB
    compression_level: int = 6  # 1-9
    compression_algorithms: List[str] = ['br', 'gzip', 'deflate']
    streaming_compression_enabled: bool = True
    
    # === API Versioning Settings ===
    api_versioning_enabled: bool = True
    default_api_version: str = "1.0"
    current_api_version: str = "1.0"
    min_api_version: str = "1.0"
    max_api_version: str = "2.0"
    version_compatibility_enabled: bool = False
    version_analytics_enabled: bool = True
    
    # === Enhanced Security Settings ===
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_headers_count: int = 100
    security_headers_enabled: bool = True
    
    # === Enhanced Performance Monitoring ===
    performance_monitoring_enabled: bool = True
    slow_request_threshold: int = 1000  # milliseconds
    memory_monitoring_enabled: bool = True
    metrics_export_enabled: bool = False
    
    # === Enhanced Logging Settings ===
    request_logging_enabled: bool = True
    log_sensitive_data: bool = False
    log_request_bodies: bool = False
    log_response_bodies: bool = False


# Middleware utility functions
def get_middleware_stats(app: FastAPI) -> Dict[str, Any]:
    """
    Get statistics and information about configured middleware.
    
    Returns:
        Dict containing middleware configuration and runtime stats
    """
    middleware_info = {
        'total_middleware': len(app.middleware_stack),
        'middleware_stack': [],
        'enabled_features': [],
        'configuration': {}
    }
    
    # Analyze middleware stack
    for middleware in app.middleware_stack:
        middleware_class = middleware.cls.__name__
        middleware_info['middleware_stack'].append(middleware_class)
        
        # Check for known middleware types
        if 'RateLimit' in middleware_class:
            middleware_info['enabled_features'].append('rate_limiting')
        elif 'Security' in middleware_class:
            middleware_info['enabled_features'].append('security_headers')
        elif 'Compression' in middleware_class:
            middleware_info['enabled_features'].append('compression')
        elif 'Versioning' in middleware_class:
            middleware_info['enabled_features'].append('api_versioning')
        elif 'Performance' in middleware_class:
            middleware_info['enabled_features'].append('performance_monitoring')
        elif 'Logging' in middleware_class:
            middleware_info['enabled_features'].append('request_logging')
        elif 'CORS' in middleware_class:
            middleware_info['enabled_features'].append('cors')
    
    return middleware_info


def validate_middleware_configuration(settings: Settings) -> List[str]:
    """
    Validate middleware configuration and return any warnings or errors.
    
    Args:
        settings: Application settings to validate
        
    Returns:
        List of validation warnings/errors
    """
    issues = []
    
    # Validate rate limiting settings
    if getattr(settings, 'rate_limiting_enabled', False):
        redis_url = getattr(settings, 'redis_url', None)
        if not redis_url:
            issues.append("Rate limiting enabled but no Redis URL configured - using local cache")
    
    # Validate compression settings
    if getattr(settings, 'compression_enabled', False):
        compression_level = getattr(settings, 'compression_level', 6)
        if not 1 <= compression_level <= 9:
            issues.append(f"Invalid compression level {compression_level}, should be 1-9")
    
    # Validate API versioning
    if getattr(settings, 'api_versioning_enabled', False):
        default_version = getattr(settings, 'default_api_version', '1.0')
        current_version = getattr(settings, 'current_api_version', '1.0')
        if not default_version or not current_version:
            issues.append("API versioning enabled but versions not properly configured")
    
    # Validate size limits
    max_request_size = getattr(settings, 'max_request_size', 0)
    if max_request_size <= 0:
        issues.append("Invalid max_request_size, should be > 0")
    
    # Validate performance monitoring
    slow_threshold = getattr(settings, 'slow_request_threshold', 1000)
    if slow_threshold <= 0:
        issues.append("Invalid slow_request_threshold, should be > 0")
    
    return issues


def create_middleware_health_check() -> Callable:
    """
    Create a health check function that validates middleware status.
    
    Returns:
        Async function that can be used as a health check endpoint
    """
    async def middleware_health_check(request: Request) -> Dict[str, Any]:
        """Check the health of all middleware components."""
        health_status = {
            'status': 'healthy',
            'middleware': {},
            'timestamp': time.time()
        }
        
        try:
            # Check if request ID is being generated (logging middleware)
            request_id = get_request_id(request)
            health_status['middleware']['request_logging'] = {
                'status': 'healthy' if request_id != 'unknown' else 'warning',
                'request_id': request_id
            }
            
            # Check performance monitoring
            duration = get_request_duration(request)
            health_status['middleware']['performance_monitoring'] = {
                'status': 'healthy' if duration is not None else 'warning',
                'request_duration_ms': duration
            }
            
            # Check API versioning
            api_version = getattr(request.state, 'api_version', None)
            health_status['middleware']['api_versioning'] = {
                'status': 'healthy' if api_version else 'not_configured',
                'detected_version': api_version
            }
            
            # Check security headers (will be added to response)
            health_status['middleware']['security'] = {
                'status': 'healthy',  # Will be verified in response headers
                'note': 'Security headers will be validated in response'
            }
            
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['error'] = str(e)
        
        return health_status
    
    return middleware_health_check


# Performance optimization functions
def optimize_middleware_stack(app: FastAPI, settings: Settings) -> None:
    """
    Optimize middleware stack for production performance.
    
    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    # Disable verbose logging in production
    if getattr(settings, 'environment', 'development') == 'production':
        # Reduce logging verbosity for performance-critical middleware
        middleware_logger = logging.getLogger('app.core.middleware')
        middleware_logger.setLevel(logging.WARNING)
        
        # Disable memory monitoring if not needed
        if not getattr(settings, 'detailed_monitoring_enabled', False):
            settings.memory_monitoring_enabled = False
        
        # Optimize compression settings for production
        if getattr(settings, 'compression_enabled', True):
            # Use faster compression in production
            settings.compression_level = min(settings.compression_level, 4)
    
    logger.info("Middleware stack optimized for production")


# Monitoring and analytics functions
def setup_middleware_monitoring(app: FastAPI, settings: Settings) -> None:
    """
    Set up monitoring and analytics for middleware performance.
    
    Args:
        app: FastAPI application instance  
        settings: Application settings
    """
    if not getattr(settings, 'middleware_monitoring_enabled', False):
        return
    
    # Set up periodic middleware health checks
    @app.on_event("startup")
    async def setup_monitoring():
        logger.info("Setting up middleware monitoring")
        
        # Could integrate with monitoring systems like:
        # - Prometheus metrics
        # - StatsD
        # - CloudWatch
        # - Custom analytics
        
        # Example: Set up periodic health checks
        async def periodic_health_check():
            while True:
                try:
                    # Check middleware health
                    stats = get_middleware_stats(app)
                    logger.info(f"Middleware health check: {stats['enabled_features']}")
                    
                    # Sleep for monitoring interval
                    await asyncio.sleep(300)  # 5 minutes
                except Exception as e:
                    logger.error(f"Middleware health check failed: {e}")
                    await asyncio.sleep(60)  # Retry in 1 minute
        
        # Start background monitoring task
        asyncio.create_task(periodic_health_check())


# Example usage and integration
def setup_production_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Set up middleware stack optimized for production use.
    
    This function configures the middleware stack with production-optimized
    settings and includes all security, performance, and monitoring features.
    
    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    # Validate configuration first
    issues = validate_middleware_configuration(settings)
    if issues:
        for issue in issues:
            logger.warning(f"Middleware configuration issue: {issue}")
    
    # Set up enhanced middleware stack
    setup_enhanced_middleware(app, settings)
    
    # Optimize for production
    optimize_middleware_stack(app, settings)
    
    # Set up monitoring
    setup_middleware_monitoring(app, settings)
    
    # Add middleware health check endpoint
    health_check_func = create_middleware_health_check()
    
    @app.get("/internal/middleware/health")
    async def middleware_health(request: Request):
        """Middleware health check endpoint."""
        return await health_check_func(request)
    
    @app.get("/internal/middleware/stats")
    async def middleware_stats():
        """Middleware statistics endpoint."""
        return get_middleware_stats(app)
    
    logger.info("Production middleware setup complete")


# Export all new components
__all__ = [
    # Enhanced setup functions
    'setup_enhanced_middleware',
    'setup_production_middleware',
    
    # New middleware classes
    'RateLimitMiddleware',
    'RequestSizeLimitMiddleware', 
    'CompressionMiddleware',
    'APIVersioningMiddleware',
    'VersionCompatibilityMiddleware',
    
    # Settings classes
    'EnhancedMiddlewareSettings',
    'RateLimitSettings',
    'CompressionSettings',
    'APIVersioningSettings',
    
    # Utility functions
    'get_middleware_stats',
    'validate_middleware_configuration',
    'create_middleware_health_check',
    'optimize_middleware_stack',
    'setup_middleware_monitoring',
    
    # Version utility functions
    'get_api_version',
    'is_version_deprecated',
    'get_version_sunset_date',
    
    # Compression utilities
    'get_compression_stats',
    'configure_compression_settings',
]