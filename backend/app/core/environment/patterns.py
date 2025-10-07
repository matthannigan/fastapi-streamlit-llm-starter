"""
Pattern matching and system indicator detection.

Contains functions and classes for detecting environment signals from:
- Environment variables
- System indicators (file presence, debug flags)
- Hostname/URL pattern matching
"""

import os
import re
import logging
from pathlib import Path
from typing import List

from .enums import Environment
from .models import EnvironmentSignal, DetectionConfig

logger = logging.getLogger(__name__)


def collect_detection_signals(config: DetectionConfig) -> List[EnvironmentSignal]:
    """
    Collect all available environment detection signals from configured sources.

    Gathers environment detection evidence from environment variables,
    system indicators, and hostname patterns. Signals are collected in
    priority order with confidence scoring for later resolution.

    Args:
        config: Detection configuration with patterns and precedence settings

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
        >>> config = DetectionConfig()
        >>> signals = collect_detection_signals(config)
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
    signals.extend(detect_from_env_vars(config))

    # 2. System indicators
    signals.extend(detect_from_system_indicators(config))

    # 3. Pattern matching on hostname/URLs
    signals.extend(detect_from_patterns(config))

    return signals


def detect_from_env_vars(config: DetectionConfig) -> List[EnvironmentSignal]:
    """
    Detect environment from environment variables using configured precedence.

    Checks environment variables in priority order, with ENVIRONMENT having
    highest precedence and framework-specific variables (NODE_ENV, FLASK_ENV)
    having lower precedence. Provides direct string-to-environment mapping.

    Args:
        config: Detection configuration with env_var_precedence settings

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
        >>> config = DetectionConfig()
        >>> # With ENVIRONMENT=production set
        >>> signals = detect_from_env_vars(config)
        >>> assert len(signals) >= 1
        >>> assert signals[0].environment == Environment.PRODUCTION
        >>> assert signals[0].confidence >= 0.95
        >>>
        >>> # With NODE_ENV=development
        >>> # (lower confidence than ENVIRONMENT)
        >>> assert any(s.confidence < 0.95 for s in signals if s.source == 'NODE_ENV')
    """
    signals = []

    for env_var in config.env_var_precedence:
        value = os.getenv(env_var)
        if not value:
            continue

        env_lower = value.lower().strip()

        # Direct environment mapping
        env_mapping = {
            "development": Environment.DEVELOPMENT,
            "dev": Environment.DEVELOPMENT,
            "testing": Environment.TESTING,
            "test": Environment.TESTING,
            "staging": Environment.STAGING,
            "stage": Environment.STAGING,
            "production": Environment.PRODUCTION,
            "prod": Environment.PRODUCTION,
            "live": Environment.PRODUCTION
        }

        if env_lower in env_mapping:
            signals.append(EnvironmentSignal(
                source=env_var,
                value=value,
                environment=env_mapping[env_lower],
                confidence=0.95 if env_var == "ENVIRONMENT" else 0.85,
                reasoning=f"Explicit environment from {env_var}={value}"
            ))

    return signals


def detect_from_system_indicators(config: DetectionConfig) -> List[EnvironmentSignal]:
    """
    Detect environment from system indicators and file presence.

    Examines system-level indicators like DEBUG flags, file presence
    (e.g., .env, .git, docker-compose files), and production indicators
    to infer the current environment context.

    Args:
        config: Detection configuration with indicator settings

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
        >>> config = DetectionConfig()
        >>> # In development environment with .env file
        >>> signals = detect_from_system_indicators(config)
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
    for indicator in config.development_indicators:
        if check_indicator(indicator):
            signals.append(EnvironmentSignal(
                source="system_indicator",
                value=indicator,
                environment=Environment.DEVELOPMENT,
                confidence=0.70,
                reasoning=f"Development indicator detected: {indicator}"
            ))

    # Production indicators
    for indicator in config.production_indicators:
        if check_indicator(indicator):
            signals.append(EnvironmentSignal(
                source="system_indicator",
                value=indicator,
                environment=Environment.PRODUCTION,
                confidence=0.75,
                reasoning=f"Production indicator detected: {indicator}"
            ))

    return signals


def check_indicator(indicator: str) -> bool:
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
        >>> # Environment variable check
        >>> # If DEBUG=true is set
        >>> assert check_indicator("DEBUG=true") == True
        >>> assert check_indicator("DEBUG=false") == False
        >>>
        >>> # File existence check
        >>> # If .env file exists in current directory
        >>> assert check_indicator(".env") == True
        >>> assert check_indicator("nonexistent.file") == False
    """
    try:
        if "=" in indicator:
            # Environment variable check
            var, expected = indicator.split("=", 1)
            return os.getenv(var, "").lower() == expected.lower()
        # File existence check
        return Path(indicator).exists()
    except (OSError, PermissionError) as e:
        # File system access errors should not break detection
        logger.warning(
            f"Unable to check system indicator '{indicator}': {e}",
            extra={"indicator": indicator, "error": str(e)}
        )
        return False


def detect_from_patterns(config: DetectionConfig) -> List[EnvironmentSignal]:
    """
    Detect environment from hostname and URL patterns.

    Applies regex pattern matching to hostname and URL values to identify
    environment context. Particularly useful in containerized deployments
    where hostname or service names follow naming conventions.

    Args:
        config: Detection configuration with pattern settings

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
        >>> config = DetectionConfig()
        >>> # With HOSTNAME=api-prod-01.example.com
        >>> signals = detect_from_patterns(config)
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
    hostname = os.getenv("HOSTNAME", "").lower()
    if hostname:
        env_patterns = [
            (config.development_patterns, Environment.DEVELOPMENT, 0.60),
            (config.staging_patterns, Environment.STAGING, 0.65),
            (config.production_patterns, Environment.PRODUCTION, 0.70)
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
