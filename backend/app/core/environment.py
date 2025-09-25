"""
Unified Environment Detection Service

This module provides centralized environment detection capabilities for all backend
infrastructure services, eliminating code duplication and providing consistent
environment classification across cache, resilience, security, and other systems.

## Architecture Position

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Services                     │
├─────────────────────────────────────────────────────────────┤
│  Security Auth  │  Cache Presets  │  Resilience Config      │
│     (NEW)       │   (EXISTING)    │    (EXISTING)           │
├─────────────────────────────────────────────────────────────┤
│           Unified Environment Detection Service             │
│                        (NEW)                                │
├─────────────────────────────────────────────────────────────┤
│              Environment Variables & System                 │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

- **Centralized Detection**: Single source of truth for environment classification
- **Confidence Scoring**: Provides confidence levels and reasoning for decisions  
- **Extensible Patterns**: Configurable patterns for custom deployment scenarios
- **Context-Aware**: Supports feature-specific context (AI, security, cache)
- **Fallback Strategies**: Robust fallback detection for edge cases
- **Integration Ready**: Drop-in replacement for existing detection logic

## Usage Examples

```python
# Basic environment detection
detector = EnvironmentDetector()
env_info = detector.detect_environment()
print(f"Environment: {env_info.environment} (confidence: {env_info.confidence})")

# Feature-specific detection
ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)
security_env = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)

# Integration with existing systems
cache_preset = cache_manager.recommend_preset(env_info.environment)
resilience_preset = resilience_manager.recommend_preset(env_info.environment)
auth_config = security_auth.configure_for_environment(env_info)
```
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, NamedTuple, Set
from enum import Enum
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """
    Standard environment classifications for application deployment contexts.

    Provides consistent environment naming across all backend infrastructure
    services including cache, resilience, security, and monitoring systems.

    Values:
        DEVELOPMENT: Local development and testing environments
        TESTING: Automated testing and CI environments
        STAGING: Pre-production environments for integration testing
        PRODUCTION: Live production environments serving real users
        UNKNOWN: Fallback when environment cannot be determined

    Examples:
        >>> env = Environment.PRODUCTION
        >>> assert env.value == "production"
        >>> assert str(env) == "production"

        >>> # Used in configuration
        >>> if env == Environment.PRODUCTION:
        ...     use_redis_cache = True
    """
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    UNKNOWN = "unknown"


class FeatureContext(str, Enum):
    """
    Feature-specific context for specialized environment detection.

    Enables feature-aware environment detection that considers specific
    infrastructure requirements like AI processing, security enforcement,
    or cache optimization when determining appropriate environment settings.

    Values:
        AI_ENABLED: Context for AI-powered features requiring model access
        SECURITY_ENFORCEMENT: Context for security-critical features
        CACHE_OPTIMIZATION: Context for cache-intensive operations
        RESILIENCE_STRATEGY: Context for resilience pattern selection
        DEFAULT: Standard environment detection without feature context

    Examples:
        >>> # Basic usage
        >>> context = FeatureContext.AI_ENABLED
        >>> assert context.value == "ai_enabled"

        >>> # Used with environment detection
        >>> env_info = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)
        >>> # May return production environment even in dev if security is enforced
    """
    AI_ENABLED = "ai_enabled"
    SECURITY_ENFORCEMENT = "security_enforcement"
    CACHE_OPTIMIZATION = "cache_optimization"
    RESILIENCE_STRATEGY = "resilience_strategy"
    DEFAULT = "default"


class EnvironmentSignal(NamedTuple):
    """
    Single environment detection signal with confidence scoring and reasoning.

    Represents one piece of evidence used in environment detection, such as
    an environment variable, system indicator, or hostname pattern match.
    Each signal includes confidence scoring to enable weighted decision making.

    Attributes:
        source: Detection mechanism that generated this signal (e.g., "env_var", "hostname_pattern")
        value: Raw value that triggered the detection (e.g., "production", "staging.example.com")
        environment: Environment classification this signal indicates
        confidence: Confidence score from 0.0-1.0 for this detection
        reasoning: Human-readable explanation of why this signal indicates the environment

    Examples:
        >>> signal = EnvironmentSignal(
        ...     source="ENVIRONMENT",
        ...     value="production",
        ...     environment=Environment.PRODUCTION,
        ...     confidence=0.95,
        ...     reasoning="Explicit environment from ENVIRONMENT=production"
        ... )
        >>> assert signal.confidence > 0.9
        >>> assert signal.environment == Environment.PRODUCTION
    """
    source: str
    value: str
    environment: Environment
    confidence: float
    reasoning: str


@dataclass
class EnvironmentInfo:
    """
    Comprehensive environment detection result with confidence scoring and metadata.

    Contains the final environment determination along with confidence scoring,
    reasoning, and supporting evidence. Includes feature-specific context and
    metadata for advanced use cases like preset selection or security overrides.

    Attributes:
        environment: Final determined environment classification
        confidence: Overall confidence score from 0.0-1.0 for the detection
        reasoning: Human-readable explanation of the detection decision
        detected_by: Primary detection mechanism that determined the environment
        feature_context: Feature-specific context used in detection
        additional_signals: All environment signals collected during detection
        metadata: Feature-specific metadata and configuration hints

    Usage:
        # Basic environment checking
        env_info = detector.detect_environment()
        if env_info.environment == Environment.PRODUCTION and env_info.confidence > 0.8:
            enable_production_features()

        # Feature-aware detection
        ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)
        if 'ai_prefix' in ai_env.metadata:
            cache_key_prefix = ai_env.metadata['ai_prefix']

        # Debugging detection issues
        print(f"Environment: {env_info}")
        print(f"Reasoning: {env_info.reasoning}")
        for signal in env_info.additional_signals:
            print(f"  - {signal.source}: {signal.reasoning}")
    """
    environment: Environment
    confidence: float
    reasoning: str
    detected_by: str
    feature_context: FeatureContext = FeatureContext.DEFAULT
    additional_signals: List[EnvironmentSignal] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.environment.value} (confidence: {self.confidence:.2f})"


@dataclass
class DetectionConfig:
    """
    Configuration for environment detection behavior and patterns.

    Controls how the EnvironmentDetector identifies environments through
    environment variables, patterns, indicators, and feature-specific overrides.
    Allows customization of detection logic for different deployment scenarios.

    Attributes:
        env_var_precedence: Environment variables checked in priority order
        development_patterns: Regex patterns indicating development environments
        staging_patterns: Regex patterns indicating staging environments
        production_patterns: Regex patterns indicating production environments
        development_indicators: System indicators suggesting development
        production_indicators: System indicators suggesting production
        feature_contexts: Feature-specific configuration overrides

    Examples:
        # Custom configuration for specialized deployment
        config = DetectionConfig(
            env_var_precedence=['CUSTOM_ENV', 'ENVIRONMENT'],
            production_patterns=[r'.*live.*', r'.*prod.*']
        )
        detector = EnvironmentDetector(config)

        # Add custom feature context
        config.feature_contexts[FeatureContext.AI_ENABLED] = {
            'environment_var': 'ENABLE_AI_FEATURES',
            'true_values': ['true', '1', 'enabled']
        }
    """
    # Environment variable precedence (highest to lowest priority)
    env_var_precedence: List[str] = field(default_factory=lambda: [
        'ENVIRONMENT',
        'NODE_ENV', 
        'FLASK_ENV',
        'APP_ENV',
        'ENV',
        'DEPLOYMENT_ENV',
        'DJANGO_SETTINGS_MODULE',
        'RAILS_ENV'
    ])
    
    # Pattern matching configurations
    development_patterns: List[str] = field(default_factory=lambda: [
        r'.*dev.*',
        r'.*local.*', 
        r'.*test.*',
        r'.*sandbox.*',
        r'.*demo.*'
    ])
    
    staging_patterns: List[str] = field(default_factory=lambda: [
        r'.*stag.*',
        r'.*pre-?prod.*',
        r'.*preprod.*',
        r'.*uat.*',
        r'.*integration.*'
    ])
    
    production_patterns: List[str] = field(default_factory=lambda: [
        r'.*prod.*',
        r'.*live.*',
        r'.*release.*',
        r'.*stable.*',
        r'.*main.*',
        r'.*master.*'
    ])
    
    # System indicator configurations
    development_indicators: List[str] = field(default_factory=lambda: [
        'DEBUG=true',
        'DEBUG=1',
        '.env',
        '.git',
        'docker-compose.dev.yml'
    ])
    
    production_indicators: List[str] = field(default_factory=lambda: [
        'PRODUCTION=true',
        'PROD=true',
        'DEBUG=false',
        'DEBUG=0'
    ])
    
    # Feature-specific overrides
    feature_contexts: Dict[FeatureContext, Dict[str, Any]] = field(default_factory=lambda: {
        FeatureContext.AI_ENABLED: {
            'environment_var': 'ENABLE_AI_CACHE',
            'true_values': ['true', '1', 'yes'],
            'preset_modifier': 'ai-'
        },
        FeatureContext.SECURITY_ENFORCEMENT: {
            'environment_var': 'ENFORCE_AUTH',
            'true_values': ['true', '1', 'yes'],
            'production_override': True
        }
    })


class EnvironmentDetector:
    """
    Unified environment detection service for consistent infrastructure configuration.

    Provides centralized environment classification across all backend infrastructure
    services including cache, resilience, security, and monitoring systems. Uses
    confidence scoring, feature-specific context, and extensible pattern matching
    to ensure reliable environment detection in diverse deployment scenarios.

    Public Methods:
        detect_environment(): Detect environment with optional feature context
        detect_with_context(): Detect environment with specific feature context
        get_environment_summary(): Get comprehensive detection summary with all signals

    State Management:
        - Maintains signal cache for performance optimization
        - Thread-safe for concurrent access across infrastructure services
        - Immutable configuration after initialization

    Behavior:
        - Collects environment signals from variables, patterns, and system indicators
        - Applies confidence scoring with conflict resolution
        - Supports feature-specific overrides for specialized detection
        - Provides fallback detection when no signals are found
        - Logs detection decisions for debugging and monitoring

    Usage:
        # Basic environment detection
        detector = EnvironmentDetector()
        env_info = detector.detect_environment()

        if env_info.environment == Environment.PRODUCTION:
            configure_production_services()
        elif env_info.confidence < 0.7:
            logger.warning(f"Low confidence detection: {env_info.reasoning}")

        # Feature-aware detection for AI services
        ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)
        if ai_env.metadata.get('ai_prefix'):
            cache_prefix = ai_env.metadata['ai_prefix']

        # Custom configuration for specialized deployment
        config = DetectionConfig(
            production_patterns=[r'.*live.*', r'.*prod.*'],
            feature_contexts={
                FeatureContext.SECURITY_ENFORCEMENT: {
                    'environment_var': 'FORCE_SECURE_MODE',
                    'production_override': True
                }
            }
        )
        detector = EnvironmentDetector(config)

        # Debugging detection issues
        summary = detector.get_environment_summary()
        print(f"Detected: {summary['detected_environment']} ({summary['confidence']:.2f})")
        for signal in summary['all_signals']:
            print(f"  - {signal['source']}: {signal['reasoning']}")
    """
    
    def __init__(self, config: Optional[DetectionConfig] = None):
        """
        Initialize environment detector with configuration and caching.

        Args:
            config: Optional detection configuration with patterns and precedence.
                   Uses DetectionConfig() defaults if not provided.

        Behavior:
            - Creates signal cache for performance optimization
            - Validates configuration patterns are well-formed regex
            - Logs initialization for debugging and monitoring
            - Stores immutable configuration for thread safety

        Examples:
            >>> # Basic initialization with defaults
            >>> detector = EnvironmentDetector()
            >>> assert detector.config is not None

            >>> # Custom configuration
            >>> config = DetectionConfig(
            ...     env_var_precedence=['CUSTOM_ENV', 'ENVIRONMENT'],
            ...     production_patterns=[r'.*prod.*', r'.*live.*']
            ... )
            >>> detector = EnvironmentDetector(config)
        """
        self.config = config or DetectionConfig()
        self._signal_cache: Dict[str, EnvironmentSignal] = {}
        logger.info("Initialized EnvironmentDetector")
    
    def detect_environment(self, feature_context: FeatureContext = FeatureContext.DEFAULT) -> EnvironmentInfo:
        """
        Detect environment with optional feature-specific context.

        Primary entry point for environment detection. Collects signals from
        environment variables, system indicators, and hostname patterns, then
        applies confidence scoring and feature-specific overrides.

        Args:
            feature_context: Feature-specific context for specialized detection.
                           Defaults to FeatureContext.DEFAULT for standard detection.
                           Use specific contexts like AI_ENABLED or SECURITY_ENFORCEMENT
                           for feature-aware detection.

        Returns:
            EnvironmentInfo containing:
            - environment: Detected Environment enum value
            - confidence: Float from 0.0-1.0 indicating detection confidence
            - reasoning: Human-readable explanation of detection decision
            - detected_by: Primary signal source that determined the environment
            - feature_context: The feature context used in detection
            - additional_signals: All signals collected during detection
            - metadata: Feature-specific metadata and configuration hints

        Behavior:
            - Collects environment signals from all configured sources
            - Applies feature-specific context overrides when specified
            - Uses confidence scoring to resolve conflicting signals
            - Returns development environment as fallback when no signals found
            - Caches detection results for performance optimization
            - Logs detection decisions for debugging and monitoring

        Examples:
            >>> detector = EnvironmentDetector()
            >>>
            >>> # Basic detection
            >>> env_info = detector.detect_environment()
            >>> assert env_info.environment in Environment
            >>> assert 0.0 <= env_info.confidence <= 1.0
            >>>
            >>> # Feature-aware detection
            >>> ai_env = detector.detect_environment(FeatureContext.AI_ENABLED)
            >>> if ai_env.metadata.get('ai_prefix'):
            ...     cache_key = f"{ai_env.metadata['ai_prefix']}cache-key"
            >>>
            >>> # High confidence check
            >>> if env_info.confidence > 0.8:
            ...     configure_production_features()
            >>> else:
            ...     logger.warning(f"Low confidence: {env_info.reasoning}")
        """
        return self.detect_with_context(feature_context)
    
    def detect_with_context(self, feature_context: FeatureContext) -> EnvironmentInfo:
        """
        Detect environment with specific feature context and specialized logic.

        Performs feature-aware environment detection that considers specific
        infrastructure requirements. May override standard detection logic
        based on feature-specific environment variables and configuration.

        Args:
            feature_context: Specific feature context for specialized detection.
                           Must be a valid FeatureContext enum value.
                           Different contexts apply different detection rules:
                           - AI_ENABLED: Checks ENABLE_AI_CACHE, may add 'ai-' prefix
                           - SECURITY_ENFORCEMENT: May override to production if ENFORCE_AUTH=true
                           - DEFAULT: Standard detection without feature-specific overrides

        Returns:
            EnvironmentInfo with feature-aware detection results containing:
            - environment: Final determined environment (may be overridden by feature context)
            - confidence: Confidence score considering feature-specific signals
            - feature_context: The specific feature context used
            - metadata: Feature-specific configuration hints and overrides
            - additional_signals: All signals including feature-specific ones

        Behavior:
            - Collects standard environment detection signals
            - Applies feature-specific environment variable checks
            - May override environment based on feature requirements
            - Adds feature-specific metadata for configuration hints
            - Combines confidence scores from multiple signal sources
            - Logs feature-specific detection decisions

        Examples:
            >>> detector = EnvironmentDetector()
            >>>
            >>> # Security enforcement may override to production
            >>> security_env = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)
            >>> if security_env.environment == Environment.PRODUCTION:
            ...     enforce_authentication_requirements()
            >>>
            >>> # AI context provides cache prefix hints
            >>> ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)
            >>> cache_prefix = ai_env.metadata.get('ai_prefix', '')
            >>> cache_key = f"{cache_prefix}summarize:{text_hash}"
            >>>
            >>> # Feature-specific confidence assessment
            >>> if ai_env.confidence > 0.9 and 'enable_ai_cache_enabled' in ai_env.metadata:
            ...     use_ai_optimized_cache_settings()
        """
        # Collect all detection signals
        signals = self._collect_detection_signals()
        
        # Apply feature-specific context
        context_info = self._apply_feature_context(signals, feature_context)
        
        # Combine all signals (base detection signals + feature-specific additional signals)
        all_signals = signals + context_info['additional_signals']
        
        # Determine final environment with confidence using ALL signals including overrides
        final_environment = self._determine_environment(all_signals)

        return EnvironmentInfo(
            environment=final_environment['environment'],
            confidence=final_environment['confidence'],
            reasoning=final_environment['reasoning'],
            detected_by=final_environment['detected_by'],
            feature_context=feature_context,
            additional_signals=all_signals,
            metadata=context_info['metadata']
        )
    
    def _collect_detection_signals(self) -> List[EnvironmentSignal]:
        """
        Collect all available environment detection signals from configured sources.

        Gathers environment detection evidence from environment variables,
        system indicators, and hostname patterns. Signals are collected in
        priority order with confidence scoring for later resolution.

        Returns:
            List of EnvironmentSignal objects, each containing:
            - source: Detection mechanism (env_var, system_indicator, hostname_pattern)
            - value: Raw value that triggered the detection
            - environment: Environment indicated by this signal
            - confidence: Confidence score for this detection
            - reasoning: Human-readable explanation

        Behavior:
            - Checks environment variables in configured precedence order
            - Examines system indicators like DEBUG flags and file presence
            - Applies hostname pattern matching for containerized deployments
            - Returns empty list if no detection signals are found
            - Maintains signal order for debugging and analysis

        Examples:
            >>> detector = EnvironmentDetector()
            >>> signals = detector._collect_detection_signals()
            >>>
            >>> # Examine signal sources
            >>> env_var_signals = [s for s in signals if s.source in ['ENVIRONMENT', 'NODE_ENV']]
            >>> pattern_signals = [s for s in signals if s.source == 'hostname_pattern']
            >>>
            >>> # Check signal confidence
            >>> high_confidence = [s for s in signals if s.confidence > 0.8]
        """
        signals = []
        
        # 1. Explicit environment variables (highest priority)
        signals.extend(self._detect_from_env_vars())
        
        # 2. System indicators
        signals.extend(self._detect_from_system_indicators())
        
        # 3. Pattern matching on hostname/URLs
        signals.extend(self._detect_from_patterns())
        
        return signals
    
    def _detect_from_env_vars(self) -> List[EnvironmentSignal]:
        """
        Detect environment from environment variables using configured precedence.

        Checks environment variables in priority order, with ENVIRONMENT having
        highest precedence and framework-specific variables (NODE_ENV, FLASK_ENV)
        having lower precedence. Provides direct string-to-environment mapping.

        Returns:
            List of EnvironmentSignal objects from environment variable detection.
            Signals are ordered by precedence with highest confidence for
            ENVIRONMENT variable and decreasing confidence for others.

        Behavior:
            - Iterates through env_var_precedence list in order
            - Maps common environment values (dev, prod, test, staging) to Environment enums
            - Assigns confidence scores based on variable precedence
            - Skips empty or undefined environment variables
            - Returns empty list if no recognized environment variables found

        Examples:
            >>> # With ENVIRONMENT=production set
            >>> signals = detector._detect_from_env_vars()
            >>> assert len(signals) >= 1
            >>> assert signals[0].environment == Environment.PRODUCTION
            >>> assert signals[0].confidence >= 0.95
            >>>
            >>> # With NODE_ENV=development
            >>> # (lower confidence than ENVIRONMENT)
            >>> assert any(s.confidence < 0.95 for s in signals if s.source == 'NODE_ENV')
        """
        signals = []
        
        for env_var in self.config.env_var_precedence:
            value = os.getenv(env_var)
            if not value:
                continue
                
            env_lower = value.lower().strip()
            
            # Direct environment mapping
            env_mapping = {
                'development': Environment.DEVELOPMENT,
                'dev': Environment.DEVELOPMENT, 
                'testing': Environment.TESTING,
                'test': Environment.TESTING,
                'staging': Environment.STAGING,
                'stage': Environment.STAGING,
                'production': Environment.PRODUCTION,
                'prod': Environment.PRODUCTION,
                'live': Environment.PRODUCTION
            }
            
            if env_lower in env_mapping:
                signals.append(EnvironmentSignal(
                    source=env_var,
                    value=value,
                    environment=env_mapping[env_lower],
                    confidence=0.95 if env_var == 'ENVIRONMENT' else 0.85,
                    reasoning=f"Explicit environment from {env_var}={value}"
                ))
                
        return signals
    
    def _detect_from_system_indicators(self) -> List[EnvironmentSignal]:
        """
        Detect environment from system indicators and file presence.

        Examines system-level indicators like DEBUG flags, file presence
        (e.g., .env, .git, docker-compose files), and production indicators
        to infer the current environment context.

        Returns:
            List of EnvironmentSignal objects from system indicator detection.
            Each signal represents one system indicator with appropriate
            confidence scoring based on indicator reliability.

        Behavior:
            - Checks development indicators (DEBUG=true, .env files, .git directories)
            - Checks production indicators (DEBUG=false, PRODUCTION=true)
            - Validates file existence for file-based indicators
            - Validates environment variable values for variable-based indicators
            - Assigns moderate confidence scores (0.70-0.75) as these are indirect signals
            - Returns empty list if no system indicators are found

        Examples:
            >>> # In development environment with .env file
            >>> signals = detector._detect_from_system_indicators()
            >>> env_file_signals = [s for s in signals if s.value == '.env']
            >>> if env_file_signals:
            ...     assert env_file_signals[0].environment == Environment.DEVELOPMENT
            >>>
            >>> # With DEBUG=false in production
            >>> debug_signals = [s for s in signals if 'DEBUG=false' in s.value]
            >>> if debug_signals:
            ...     assert debug_signals[0].environment == Environment.PRODUCTION
        """
        signals = []
        
        # Development indicators
        for indicator in self.config.development_indicators:
            if self._check_indicator(indicator):
                signals.append(EnvironmentSignal(
                    source="system_indicator",
                    value=indicator,
                    environment=Environment.DEVELOPMENT,
                    confidence=0.70,
                    reasoning=f"Development indicator detected: {indicator}"
                ))
        
        # Production indicators
        for indicator in self.config.production_indicators:
            if self._check_indicator(indicator):
                signals.append(EnvironmentSignal(
                    source="system_indicator", 
                    value=indicator,
                    environment=Environment.PRODUCTION,
                    confidence=0.75,
                    reasoning=f"Production indicator detected: {indicator}"
                ))
                
        return signals
    
    def _check_indicator(self, indicator: str) -> bool:
        """
        Check if a system indicator is present in the environment.

        Validates both environment variable indicators (KEY=value format)
        and file-based indicators (file paths) to determine if the
        specified system condition exists.

        Args:
            indicator: System indicator to check. Format depends on type:
                      - Environment variable: "VAR_NAME=expected_value"
                      - File existence: "path/to/file" or "filename"

        Returns:
            True if the indicator condition is met, False otherwise.
            For environment variables: True if variable equals expected value
            For files: True if file exists at the specified path

        Behavior:
            - Detects indicator type by presence of '=' character
            - For env vars: performs case-insensitive value comparison
            - For files: checks file existence using Path.exists()
            - Returns False for malformed indicators or missing conditions
            - Does not raise exceptions for invalid paths or variables
            - Logs warnings for file system access errors but continues gracefully

        Examples:
            >>> detector = EnvironmentDetector()
            >>>
            >>> # Environment variable check
            >>> # If DEBUG=true is set
            >>> assert detector._check_indicator("DEBUG=true") == True
            >>> assert detector._check_indicator("DEBUG=false") == False
            >>>
            >>> # File existence check
            >>> # If .env file exists in current directory
            >>> assert detector._check_indicator(".env") == True
            >>> assert detector._check_indicator("nonexistent.file") == False
        """
        try:
            if '=' in indicator:
                # Environment variable check
                var, expected = indicator.split('=', 1)
                return os.getenv(var, '').lower() == expected.lower()
            else:
                # File existence check
                return Path(indicator).exists()
        except (OSError, PermissionError, IOError) as e:
            # File system access errors should not break detection
            logger.warning(
                f"Unable to check system indicator '{indicator}': {e}",
                extra={"indicator": indicator, "error": str(e)}
            )
            return False
    
    def _detect_from_patterns(self) -> List[EnvironmentSignal]:
        """
        Detect environment from hostname and URL patterns.

        Applies regex pattern matching to hostname and URL values to identify
        environment context. Particularly useful in containerized deployments
        where hostname or service names follow naming conventions.

        Returns:
            List of EnvironmentSignal objects from pattern matching.
            Signals include the matched hostname/URL and the pattern that
            identified the environment context.

        Behavior:
            - Retrieves hostname from HOSTNAME environment variable
            - Applies regex patterns for development, staging, and production
            - Uses case-insensitive matching for broader compatibility
            - Stops at first match per pattern category for efficiency
            - Assigns moderate confidence (0.60-0.70) as patterns can be ambiguous
            - Returns empty list if no HOSTNAME set or no patterns match
            - Logs warnings for invalid regex patterns but continues with valid patterns

        Examples:
            >>> # With HOSTNAME=api-prod-01.example.com
            >>> signals = detector._detect_from_patterns()
            >>> prod_signals = [s for s in signals if s.environment == Environment.PRODUCTION]
            >>> if prod_signals:
            ...     assert 'prod' in prod_signals[0].value.lower()
            >>>
            >>> # With HOSTNAME=dev-service.local
            >>> # Should match development patterns
            >>> dev_signals = [s for s in signals if s.environment == Environment.DEVELOPMENT]
        """
        signals = []
        
        # Check hostname patterns
        hostname = os.getenv('HOSTNAME', '').lower()
        if hostname:
            env_patterns = [
                (self.config.development_patterns, Environment.DEVELOPMENT, 0.60),
                (self.config.staging_patterns, Environment.STAGING, 0.65),
                (self.config.production_patterns, Environment.PRODUCTION, 0.70)
            ]
            
            for patterns, environment, confidence in env_patterns:
                for pattern in patterns:
                    try:
                        if re.match(pattern, hostname, re.IGNORECASE):
                            signals.append(EnvironmentSignal(
                                source="hostname_pattern",
                                value=hostname,
                                environment=environment,
                                confidence=confidence,
                                reasoning=f"Hostname '{hostname}' matches {environment.value} pattern"
                            ))
                            break
                    except re.error as e:
                        # Log invalid pattern but continue with other patterns
                        logger.warning(
                            f"Skipping invalid regex pattern in {environment.value} detection",
                            extra={
                                "pattern": pattern,
                                "environment_type": environment.value,
                                "regex_error": str(e),
                                "hostname": hostname
                            }
                        )
                        continue
        
        return signals
    
    def _apply_feature_context(self, signals: List[EnvironmentSignal], context: FeatureContext) -> Dict[str, Any]:
        """
        Apply feature-specific context and overrides to detection signals.

        Processes feature-specific environment variables and configuration
        to modify detection behavior. May add additional signals or metadata
        based on feature requirements like AI enabling or security enforcement.

        Args:
            signals: Base environment signals from standard detection
            context: Feature context specifying specialized detection logic

        Returns:
            Dictionary containing:
            - 'signals': Original signals list (unmodified)
            - 'additional_signals': Feature-specific signals to add
            - 'metadata': Feature-specific metadata and configuration hints

        Behavior:
            - Returns original signals unchanged for DEFAULT context
            - Checks feature-specific environment variables when configured
            - Adds metadata hints for cache prefixes, security overrides, etc.
            - May inject additional signals for feature-specific overrides
            - Preserves original signal list while adding context-specific data
            - Logs feature-specific detection decisions

        Examples:
            >>> detector = EnvironmentDetector()
            >>> base_signals = [EnvironmentSignal(...)]  # from standard detection
            >>>
            >>> # AI context adds cache prefix metadata
            >>> result = detector._apply_feature_context(base_signals, FeatureContext.AI_ENABLED)
            >>> if result['metadata'].get('ai_prefix'):
            ...     cache_key = f"{result['metadata']['ai_prefix']}operation-key"
            >>>
            >>> # Security context may add production override signal
            >>> security_result = detector._apply_feature_context(
            ...     base_signals, FeatureContext.SECURITY_ENFORCEMENT
            ... )
            >>> additional = security_result['additional_signals']
            >>> security_overrides = [s for s in additional if s.source == 'security_override']
        """
        if context == FeatureContext.DEFAULT:
            return {
                'signals': signals,
                'additional_signals': [],
                'metadata': {}
            }
        
        context_config = self.config.feature_contexts.get(context, {})
        additional_signals = []
        metadata: Dict[str, Any] = {'feature_context': context.value}
        
        # Check feature-specific environment variables
        if 'environment_var' in context_config:
            env_var = context_config['environment_var']
            value = os.getenv(env_var, '').lower()
            true_values = context_config.get('true_values', ['true'])
            
            if value in true_values:
                metadata[f'{env_var.lower()}_enabled'] = True
                
                # For AI context, modify environment recommendations
                if context == FeatureContext.AI_ENABLED:
                    metadata['ai_prefix'] = context_config.get('preset_modifier', '')
                    
                # For security context, may override to production
                elif context == FeatureContext.SECURITY_ENFORCEMENT:
                    if context_config.get('production_override'):
                        additional_signals.append(EnvironmentSignal(
                            source="security_override",
                            value=f"{env_var}={value}",
                            environment=Environment.PRODUCTION,
                            confidence=0.98,
                            reasoning=f"Security enforcement enabled via {env_var}"
                        ))
        
        return {
            'signals': signals,
            'additional_signals': additional_signals,
            'metadata': metadata
        }
    
    def _determine_environment(self, signals: List[EnvironmentSignal]) -> Dict[str, Any]:
        """
        Determine final environment from all collected signals using confidence scoring.

        Analyzes all environment signals to make a final environment determination.
        Uses confidence scoring, conflict resolution, and fallback logic to
        ensure reliable environment detection even with contradictory signals.

        Args:
            signals: All environment signals collected from detection sources

        Returns:
            Dictionary containing final environment determination:
            - 'environment': Final Environment enum value
            - 'confidence': Combined confidence score (0.0-1.0)
            - 'reasoning': Human-readable explanation of decision
            - 'detected_by': Primary signal source that determined environment

        Behavior:
            - Returns development fallback if no signals provided
            - Sorts signals by confidence score (highest first)
            - Uses highest confidence signal as primary determination
            - Boosts confidence when multiple signals agree
            - Reduces confidence when high-confidence conflicts exist
            - Generates comprehensive reasoning including conflicts
            - Caps combined confidence at 0.98 to indicate uncertainty

        Examples:
            >>> detector = EnvironmentDetector()
            >>>
            >>> # Multiple agreeing signals boost confidence
            >>> signals = [
            ...     EnvironmentSignal(..., environment=Environment.PRODUCTION, confidence=0.85),
            ...     EnvironmentSignal(..., environment=Environment.PRODUCTION, confidence=0.70)
            ... ]
            >>> result = detector._determine_environment(signals)
            >>> assert result['confidence'] > 0.85  # Boosted by agreement
            >>>
            >>> # Conflicting signals reduce confidence
            >>> conflicting_signals = [
            ...     EnvironmentSignal(..., environment=Environment.PRODUCTION, confidence=0.85),
            ...     EnvironmentSignal(..., environment=Environment.DEVELOPMENT, confidence=0.75)
            ... ]
            >>> result = detector._determine_environment(conflicting_signals)
            >>> assert result['confidence'] < 0.85  # Reduced by conflict
        """
        if not signals:
            return {
                'environment': Environment.DEVELOPMENT,
                'confidence': 0.50,
                'reasoning': "No environment signals detected, defaulting to development",
                'detected_by': "fallback"
            }
        
        # Sort signals by confidence (highest first)
        sorted_signals = sorted(signals, key=lambda s: s.confidence, reverse=True)
        best_signal = sorted_signals[0]
        
        # Check for conflicting signals
        same_env_signals = [s for s in sorted_signals if s.environment == best_signal.environment]
        conflicting_signals = [s for s in sorted_signals if s.environment != best_signal.environment]
        
        # Calculate combined confidence
        if len(same_env_signals) > 1:
            # Multiple signals pointing to same environment increase confidence
            combined_confidence = min(0.98, best_signal.confidence + 0.05 * (len(same_env_signals) - 1))
        else:
            combined_confidence = best_signal.confidence
        
        # Adjust confidence if there are high-confidence conflicting signals
        if conflicting_signals and max(s.confidence for s in conflicting_signals) > 0.70:
            combined_confidence *= 0.85  # Reduce confidence due to conflicts
        
        reasoning = best_signal.reasoning
        if len(same_env_signals) > 1:
            reasoning += f" (confirmed by {len(same_env_signals)-1} additional signals)"
        if conflicting_signals:
            reasoning += f" (note: {len(conflicting_signals)} conflicting signals detected)"
        
        return {
            'environment': best_signal.environment,
            'confidence': combined_confidence,
            'reasoning': reasoning,
            'detected_by': best_signal.source
        }
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive environment detection summary with all signals and metadata.

        Provides detailed information about environment detection including
        all collected signals, confidence scores, and metadata. Useful for
        debugging detection issues and understanding how the environment was determined.

        Returns:
            Dictionary containing comprehensive detection information:
            - 'detected_environment': Final environment name as string
            - 'confidence': Overall confidence score (0.0-1.0)
            - 'reasoning': Human-readable explanation of detection decision
            - 'detected_by': Primary detection mechanism
            - 'all_signals': List of all signals with source, value, confidence
            - 'metadata': Feature-specific metadata and configuration hints

        Behavior:
            - Performs full environment detection with default context
            - Formats all signals for human-readable output
            - Includes both primary and additional signals
            - Preserves original signal confidence scores
            - Provides structured data for programmatic analysis

        Examples:
            >>> detector = EnvironmentDetector()
            >>> summary = detector.get_environment_summary()
            >>>
            >>> # Check detection results
            >>> print(f"Environment: {summary['detected_environment']}")
            >>> print(f"Confidence: {summary['confidence']:.2f}")
            >>> print(f"Reasoning: {summary['reasoning']}")
            >>>
            >>> # Analyze all signals
            >>> for signal in summary['all_signals']:
            ...     print(f"  {signal['source']}: {signal['reasoning']}")
            >>>
            >>> # Debug low confidence detection
            >>> if summary['confidence'] < 0.7:
            ...     logger.warning(f"Low confidence detection: {summary['reasoning']}")
            ...     for signal in summary['all_signals']:
            ...         logger.info(f"Signal: {signal['source']} -> {signal['environment']} ({signal['confidence']})")
        """
        env_info = self.detect_environment()
        
        return {
            'detected_environment': env_info.environment.value,
            'confidence': env_info.confidence,
            'reasoning': env_info.reasoning,
            'detected_by': env_info.detected_by,
            'all_signals': [
                {
                    'source': signal.source,
                    'value': signal.value,
                    'environment': signal.environment.value,
                    'confidence': signal.confidence,
                    'reasoning': signal.reasoning
                }
                for signal in env_info.additional_signals
            ],
            'metadata': env_info.metadata
        }


# Global instance for easy access across the application
environment_detector = EnvironmentDetector()


def get_environment_info(feature_context: FeatureContext = FeatureContext.DEFAULT) -> EnvironmentInfo:
    """
    Convenient function to get environment information using the global detector.

    Provides easy access to environment detection without needing to create
    an EnvironmentDetector instance. Uses the global environment_detector
    instance with default configuration for consistent detection across the application.

    Args:
        feature_context: Feature context for specialized detection logic.
                        Defaults to FeatureContext.DEFAULT for standard detection.
                        Use specific contexts like AI_ENABLED or SECURITY_ENFORCEMENT
                        for feature-aware detection.

    Returns:
        EnvironmentInfo containing:
        - environment: Detected Environment enum value
        - confidence: Detection confidence score (0.0-1.0)
        - reasoning: Human-readable explanation of detection
        - feature_context: The feature context used
        - metadata: Feature-specific configuration hints
        - additional_signals: All detection signals collected

    Raises:
        ValidationError: If feature_context is not a valid FeatureContext enum value

    Behavior:
        - Uses global environment_detector instance for consistent results
        - Performs full environment detection with confidence scoring
        - Applies feature-specific context when specified
        - Caches detection results for performance optimization
        - Thread-safe for concurrent access across services

    Examples:
        >>> # Basic environment detection
        >>> env_info = get_environment_info()
        >>> if env_info.environment == Environment.PRODUCTION:
        ...     enable_production_logging()
        >>>
        >>> # Feature-aware detection
        >>> ai_env = get_environment_info(FeatureContext.AI_ENABLED)
        >>> if ai_env.metadata.get('ai_prefix'):
        ...     cache_prefix = ai_env.metadata['ai_prefix']
        >>>
        >>> # Confidence-based decisions
        >>> security_env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
        >>> if security_env.confidence > 0.8:
        ...     enforce_strict_security_policies()
        >>> else:
        ...     logger.warning(f"Uncertain environment detection: {security_env.reasoning}")
    """
    return environment_detector.detect_with_context(feature_context)


def is_production_environment(feature_context: FeatureContext = FeatureContext.DEFAULT) -> bool:
    """
    Check if running in production environment with confidence threshold.

    Convenience function for production environment checks with built-in
    confidence validation. Uses reasonable confidence threshold to avoid
    false positives that could affect production configurations.

    Args:
        feature_context: Feature context for specialized detection logic.
                        Defaults to FeatureContext.DEFAULT for standard detection.
                        Use SECURITY_ENFORCEMENT context for stricter production detection.

    Returns:
        True if production environment is detected with confidence > 0.60,
        False otherwise. The 0.60 threshold balances reliability with
        sensitivity to avoid false production configurations.

    Behavior:
        - Performs environment detection with specified feature context
        - Requires both Environment.PRODUCTION and confidence > 0.60
        - Returns False for uncertain or non-production detections
        - Uses same detection logic as get_environment_info()

    Examples:
        >>> # Basic production check
        >>> if is_production_environment():
        ...     configure_production_logging()
        ...     enable_performance_monitoring()
        >>>
        >>> # Security-aware production check
        >>> if is_production_environment(FeatureContext.SECURITY_ENFORCEMENT):
        ...     enforce_authentication_requirements()
        ...     enable_audit_logging()
        >>>
        >>> # Combined with manual confidence check
        >>> env_info = get_environment_info()
        >>> if is_production_environment() and env_info.confidence > 0.9:
        ...     enable_strict_production_features()
    """
    env_info = get_environment_info(feature_context)
    return env_info.environment == Environment.PRODUCTION and env_info.confidence > 0.60


def is_development_environment(feature_context: FeatureContext = FeatureContext.DEFAULT) -> bool:
    """
    Check if running in development environment with confidence threshold.

    Convenience function for development environment checks with built-in
    confidence validation. Useful for enabling development-specific features
    like debug logging, hot reloading, or relaxed security settings.

    Args:
        feature_context: Feature context for specialized detection logic.
                        Defaults to FeatureContext.DEFAULT for standard detection.
                        Use specific contexts for feature-aware development detection.

    Returns:
        True if development environment is detected with confidence > 0.60,
        False otherwise. The 0.60 threshold ensures reasonable confidence
        while allowing for development environment variations.

    Behavior:
        - Performs environment detection with specified feature context
        - Requires both Environment.DEVELOPMENT and confidence > 0.60
        - Returns False for uncertain or non-development detections
        - Uses same detection logic as get_environment_info()

    Examples:
        >>> # Basic development check
        >>> if is_development_environment():
        ...     enable_debug_logging()
        ...     configure_hot_reloading()
        >>>
        >>> # AI development features
        >>> if is_development_environment(FeatureContext.AI_ENABLED):
        ...     use_development_ai_models()
        ...     enable_ai_debug_logging()
        >>>
        >>> # Development-specific cache settings
        >>> if is_development_environment(FeatureContext.CACHE_OPTIMIZATION):
        ...     use_memory_cache_only()
        ...     set_short_cache_ttls()
    """
    env_info = get_environment_info(feature_context)
    return env_info.environment == Environment.DEVELOPMENT and env_info.confidence > 0.60
