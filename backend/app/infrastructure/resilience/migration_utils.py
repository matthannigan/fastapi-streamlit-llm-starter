"""
Configuration migration utilities for legacy-to-preset migration.

This module provides tools to analyze legacy resilience configurations
and recommend appropriate preset replacements with migration guidance.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MigrationConfidence(Enum):
    """Confidence levels for migration recommendations."""
    HIGH = "high"      # 90%+ certainty, direct mapping
    MEDIUM = "medium"  # 70-89% certainty, mostly compatible
    LOW = "low"        # 50-69% certainty, requires review


@dataclass
class MigrationRecommendation:
    """Recommendation for migrating from legacy to preset configuration."""
    recommended_preset: str
    confidence: MigrationConfidence
    reasoning: str
    custom_overrides: Optional[Dict[str, Any]] = None
    warnings: List[str] = None
    migration_steps: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.migration_steps is None:
            self.migration_steps = []


class LegacyConfigAnalyzer:
    """Analyzer for legacy resilience configuration patterns."""
    
    # Mapping from legacy environment variables to modern equivalents
    LEGACY_VAR_MAPPING = {
        "RETRY_MAX_ATTEMPTS": "retry_attempts",
        "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "circuit_breaker_threshold",
        "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "recovery_timeout",
        "DEFAULT_RESILIENCE_STRATEGY": "default_strategy",
        "RETRY_MAX_DELAY": "max_delay_seconds",
        "RETRY_EXPONENTIAL_MULTIPLIER": "exponential_multiplier",
        "RETRY_EXPONENTIAL_MIN": "exponential_min",
        "RETRY_EXPONENTIAL_MAX": "exponential_max",
        "RETRY_JITTER_ENABLED": "jitter_enabled",
        "RETRY_JITTER_MAX": "jitter_max",
        
        # Operation-specific strategies
        "SUMMARIZE_RESILIENCE_STRATEGY": "operation_overrides.summarize",
        "SENTIMENT_RESILIENCE_STRATEGY": "operation_overrides.sentiment",
        "KEY_POINTS_RESILIENCE_STRATEGY": "operation_overrides.key_points",
        "QUESTIONS_RESILIENCE_STRATEGY": "operation_overrides.questions",
        "QA_RESILIENCE_STRATEGY": "operation_overrides.qa",
    }
    
    def __init__(self):
        """Initialize the legacy configuration analyzer."""
        pass
    
    def detect_legacy_configuration(self, env_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Detect legacy resilience configuration from environment variables.
        
        Args:
            env_vars: Environment variables to analyze (if None, uses os.environ)
            
        Returns:
            Dictionary of detected legacy configuration values
        """
        if env_vars is None:
            env_vars = dict(os.environ)
        
        legacy_config = {}
        
        for legacy_var, modern_key in self.LEGACY_VAR_MAPPING.items():
            if legacy_var in env_vars:
                value = env_vars[legacy_var]
                
                # Convert values to appropriate types
                if legacy_var in ["RETRY_MAX_ATTEMPTS", "CIRCUIT_BREAKER_FAILURE_THRESHOLD", 
                                 "CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "RETRY_MAX_DELAY"]:
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning(f"Invalid integer value for {legacy_var}: {value}")
                        continue
                
                elif legacy_var in ["RETRY_EXPONENTIAL_MULTIPLIER", "RETRY_EXPONENTIAL_MIN", 
                                  "RETRY_EXPONENTIAL_MAX", "RETRY_JITTER_MAX"]:
                    try:
                        value = float(value)
                    except ValueError:
                        logger.warning(f"Invalid float value for {legacy_var}: {value}")
                        continue
                
                elif legacy_var == "RETRY_JITTER_ENABLED":
                    value = value.lower() in ("true", "1", "yes", "on")
                
                # Handle nested keys (operation_overrides)
                if "." in modern_key:
                    parts = modern_key.split(".")
                    if parts[0] not in legacy_config:
                        legacy_config[parts[0]] = {}
                    legacy_config[parts[0]][parts[1]] = value
                else:
                    legacy_config[modern_key] = value
        
        logger.info(f"Detected legacy configuration with {len(legacy_config)} settings")
        return legacy_config
    
    def recommend_preset(self, legacy_config: Dict[str, Any]) -> MigrationRecommendation:
        """
        Recommend appropriate preset based on legacy configuration analysis.
        
        Args:
            legacy_config: Detected legacy configuration
            
        Returns:
            Migration recommendation with preset, confidence, and guidance
        """
        if not legacy_config:
            return MigrationRecommendation(
                recommended_preset="simple",
                confidence=MigrationConfidence.HIGH,
                reasoning="No legacy configuration detected, simple preset is ideal for new setups",
                migration_steps=["Set RESILIENCE_PRESET=simple", "Remove any legacy environment variables"]
            )
        
        # Score each preset based on configuration similarity
        preset_scores = self._calculate_preset_scores(legacy_config)
        
        # Get best matching preset
        best_preset = max(preset_scores, key=preset_scores.get)
        score = preset_scores[best_preset]
        
        # Determine confidence based on score
        if score >= 0.9:
            confidence = MigrationConfidence.HIGH
        elif score >= 0.7:
            confidence = MigrationConfidence.MEDIUM
        else:
            confidence = MigrationConfidence.LOW
        
        # Generate custom overrides for values that don't match preset defaults
        custom_overrides = self._generate_custom_overrides(legacy_config, best_preset)
        
        # Generate warnings for potentially problematic configurations
        warnings = self._generate_migration_warnings(legacy_config)
        
        # Generate step-by-step migration instructions
        migration_steps = self._generate_migration_steps(best_preset, custom_overrides)
        
        reasoning = self._generate_reasoning(legacy_config, best_preset, score)
        
        return MigrationRecommendation(
            recommended_preset=best_preset,
            confidence=confidence,
            reasoning=reasoning,
            custom_overrides=custom_overrides,
            warnings=warnings,
            migration_steps=migration_steps
        )
    
    def _calculate_preset_scores(self, legacy_config: Dict[str, Any]) -> Dict[str, float]:
        """Calculate compatibility scores for each preset."""
        from app.infrastructure.resilience.presets import PRESETS
        
        scores = {}
        
        for preset_name, preset in PRESETS.items():
            score = 0.0
            total_weight = 0.0
            
            # Score retry attempts (weight: 0.3)
            if "retry_attempts" in legacy_config:
                weight = 0.3
                legacy_val = legacy_config["retry_attempts"]
                preset_val = preset.retry_attempts
                # Score based on how close values are (0-1 scale)
                diff = abs(legacy_val - preset_val) / max(legacy_val, preset_val, 1)
                score += weight * (1 - min(diff, 1))
                total_weight += weight
            
            # Score circuit breaker threshold (weight: 0.25)
            if "circuit_breaker_threshold" in legacy_config:
                weight = 0.25
                legacy_val = legacy_config["circuit_breaker_threshold"]
                preset_val = preset.circuit_breaker_threshold
                diff = abs(legacy_val - preset_val) / max(legacy_val, preset_val, 1)
                score += weight * (1 - min(diff, 1))
                total_weight += weight
            
            # Score recovery timeout (weight: 0.2)
            if "recovery_timeout" in legacy_config:
                weight = 0.2
                legacy_val = legacy_config["recovery_timeout"]
                preset_val = preset.recovery_timeout
                diff = abs(legacy_val - preset_val) / max(legacy_val, preset_val, 1)
                score += weight * (1 - min(diff, 1))
                total_weight += weight
            
            # Score default strategy (weight: 0.15)
            if "default_strategy" in legacy_config:
                weight = 0.15
                if legacy_config["default_strategy"] == preset.default_strategy.value:
                    score += weight
                total_weight += weight
            
            # Score operation overrides (weight: 0.1)
            legacy_overrides = legacy_config.get("operation_overrides", {})
            if legacy_overrides:
                weight = 0.1
                matches = 0
                total_ops = len(legacy_overrides)
                
                for op, strategy in legacy_overrides.items():
                    if op in preset.operation_overrides:
                        if preset.operation_overrides[op].value == strategy:
                            matches += 1
                    elif strategy == preset.default_strategy.value:
                        matches += 1  # Matches default
                
                if total_ops > 0:
                    score += weight * (matches / total_ops)
                total_weight += weight
            
            # Normalize score
            if total_weight > 0:
                scores[preset_name] = score / total_weight
            else:
                scores[preset_name] = 0.5  # Neutral score if no comparison possible
        
        return scores
    
    def _generate_custom_overrides(self, legacy_config: Dict[str, Any], preset_name: str) -> Optional[Dict[str, Any]]:
        """Generate custom configuration overrides for values that don't match preset."""
        from app.infrastructure.resilience.presets import PRESETS
        
        if preset_name not in PRESETS:
            return None
        
        preset = PRESETS[preset_name]
        overrides = {}
        
        # Check if any values differ significantly from preset defaults
        if "retry_attempts" in legacy_config:
            if legacy_config["retry_attempts"] != preset.retry_attempts:
                overrides["retry_attempts"] = legacy_config["retry_attempts"]
        
        if "circuit_breaker_threshold" in legacy_config:
            if legacy_config["circuit_breaker_threshold"] != preset.circuit_breaker_threshold:
                overrides["circuit_breaker_threshold"] = legacy_config["circuit_breaker_threshold"]
        
        if "recovery_timeout" in legacy_config:
            if legacy_config["recovery_timeout"] != preset.recovery_timeout:
                overrides["recovery_timeout"] = legacy_config["recovery_timeout"]
        
        if "default_strategy" in legacy_config:
            if legacy_config["default_strategy"] != preset.default_strategy.value:
                overrides["default_strategy"] = legacy_config["default_strategy"]
        
        # Handle operation overrides
        legacy_overrides = legacy_config.get("operation_overrides", {})
        if legacy_overrides:
            operation_overrides = {}
            for op, strategy in legacy_overrides.items():
                # Only include if different from preset's operation override or default
                preset_strategy = None
                if op in preset.operation_overrides:
                    preset_strategy = preset.operation_overrides[op].value
                else:
                    preset_strategy = preset.default_strategy.value
                
                if strategy != preset_strategy:
                    operation_overrides[op] = strategy
            
            if operation_overrides:
                overrides["operation_overrides"] = operation_overrides
        
        # Include other custom parameters that don't have preset equivalents
        for key in ["max_delay_seconds", "exponential_multiplier", "exponential_min", 
                   "exponential_max", "jitter_enabled", "jitter_max"]:
            if key in legacy_config:
                overrides[key] = legacy_config[key]
        
        return overrides if overrides else None
    
    def _generate_migration_warnings(self, legacy_config: Dict[str, Any]) -> List[str]:
        """Generate warnings for potentially problematic configurations."""
        warnings = []
        
        # Check for potentially problematic values
        retry_attempts = legacy_config.get("retry_attempts")
        if retry_attempts and retry_attempts > 7:
            warnings.append(f"High retry attempts ({retry_attempts}) may cause significant latency")
        
        circuit_threshold = legacy_config.get("circuit_breaker_threshold")
        if circuit_threshold and circuit_threshold < 3:
            warnings.append(f"Low circuit breaker threshold ({circuit_threshold}) may cause frequent failures")
        
        # Check for mismatched retry/circuit breaker settings
        if retry_attempts and circuit_threshold and retry_attempts > circuit_threshold:
            warnings.append("Retry attempts exceed circuit breaker threshold - circuit may open before retries complete")
        
        # Check for aggressive strategies in what might be production
        if legacy_config.get("default_strategy") == "aggressive":
            warnings.append("Aggressive strategy detected - ensure this is appropriate for your environment")
        
        return warnings
    
    def _generate_migration_steps(self, preset_name: str, custom_overrides: Optional[Dict[str, Any]]) -> List[str]:
        """Generate step-by-step migration instructions."""
        steps = [
            f"1. Set environment variable: RESILIENCE_PRESET={preset_name}",
            "2. Remove legacy resilience environment variables:"
        ]
        
        # List legacy variables to remove
        legacy_vars = list(self.LEGACY_VAR_MAPPING.keys())
        for i, var in enumerate(legacy_vars):
            steps.append(f"   - {var}")
        
        if custom_overrides:
            steps.append("3. Add custom configuration overrides:")
            override_json = json.dumps(custom_overrides, indent=2)
            steps.append(f"   RESILIENCE_CUSTOM_CONFIG='{override_json}'")
        else:
            steps.append("3. No custom overrides needed - preset defaults are sufficient")
        
        steps.extend([
            "4. Test the new configuration in a development environment",
            "5. Monitor resilience metrics after deployment",
            "6. Fine-tune custom overrides if needed based on performance"
        ])
        
        return steps
    
    def _generate_reasoning(self, legacy_config: Dict[str, Any], preset_name: str, score: float) -> str:
        """Generate human-readable reasoning for the recommendation."""
        reasoning_parts = [
            f"Based on analysis of your legacy configuration, '{preset_name}' preset is the best match "
            f"(compatibility score: {score:.1%})."
        ]
        
        # Add specific reasoning based on detected patterns
        retry_attempts = legacy_config.get("retry_attempts")
        circuit_threshold = legacy_config.get("circuit_breaker_threshold")
        strategy = legacy_config.get("default_strategy")
        
        if preset_name == "development":
            reasoning_parts.append("Your configuration shows patterns typical of development environments: "
                                 "fast failure recovery and aggressive retry strategies.")
        elif preset_name == "production":
            reasoning_parts.append("Your configuration emphasizes reliability and fault tolerance, "
                                 "indicating production-grade requirements.")
        elif preset_name == "simple":
            reasoning_parts.append("Your configuration uses balanced settings suitable for general use cases.")
        
        if retry_attempts:
            reasoning_parts.append(f"Retry attempts ({retry_attempts}) align well with {preset_name} preset expectations.")
        
        if circuit_threshold:
            reasoning_parts.append(f"Circuit breaker threshold ({circuit_threshold}) is compatible with {preset_name} reliability requirements.")
        
        if strategy:
            reasoning_parts.append(f"Default strategy '{strategy}' matches {preset_name} preset philosophy.")
        
        return " ".join(reasoning_parts)


class ConfigurationMigrator:
    """Tool for performing automated configuration migrations."""
    
    def __init__(self):
        """Initialize the configuration migrator."""
        self.analyzer = LegacyConfigAnalyzer()
    
    def analyze_current_environment(self) -> MigrationRecommendation:
        """Analyze current environment and provide migration recommendation."""
        legacy_config = self.analyzer.detect_legacy_configuration()
        return self.analyzer.recommend_preset(legacy_config)
    
    def generate_migration_script(self, recommendation: MigrationRecommendation, 
                                output_format: str = "bash") -> str:
        """
        Generate migration script in specified format.
        
        Args:
            recommendation: Migration recommendation to implement
            output_format: Script format ('bash', 'env', 'docker')
            
        Returns:
            Generated migration script content
        """
        if output_format == "bash":
            return self._generate_bash_script(recommendation)
        elif output_format == "env":
            return self._generate_env_file(recommendation)
        elif output_format == "docker":
            return self._generate_docker_env(recommendation)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_bash_script(self, recommendation: MigrationRecommendation) -> str:
        """Generate bash script for migration."""
        script_lines = [
            "#!/bin/bash",
            "# Resilience Configuration Migration Script",
            f"# Migrating to preset: {recommendation.recommended_preset}",
            f"# Confidence: {recommendation.confidence.value}",
            "",
            "echo 'Starting resilience configuration migration...'",
            "",
            "# Set new preset configuration",
            f"export RESILIENCE_PRESET={recommendation.recommended_preset}",
            "",
            "# Remove legacy environment variables",
        ]
        
        for legacy_var in self.analyzer.LEGACY_VAR_MAPPING.keys():
            script_lines.append(f"unset {legacy_var}")
        
        if recommendation.custom_overrides:
            script_lines.extend([
                "",
                "# Set custom configuration overrides",
                f"export RESILIENCE_CUSTOM_CONFIG='{json.dumps(recommendation.custom_overrides)}'"
            ])
        
        script_lines.extend([
            "",
            "echo 'Migration completed!'",
            "echo 'Please test your application with the new configuration.'"
        ])
        
        if recommendation.warnings:
            script_lines.extend([
                "",
                "echo 'WARNINGS:'",
            ])
            for warning in recommendation.warnings:
                script_lines.append(f"echo '  - {warning}'")
        
        return "\n".join(script_lines)
    
    def _generate_env_file(self, recommendation: MigrationRecommendation) -> str:
        """Generate .env file format."""
        env_lines = [
            "# Resilience Configuration (Preset-based)",
            f"# Generated migration to: {recommendation.recommended_preset}",
            "",
            f"RESILIENCE_PRESET={recommendation.recommended_preset}",
        ]
        
        if recommendation.custom_overrides:
            env_lines.extend([
                "",
                "# Custom configuration overrides",
                f"RESILIENCE_CUSTOM_CONFIG='{json.dumps(recommendation.custom_overrides, separators=(',', ':'))}'",
            ])
        
        env_lines.extend([
            "",
            "# Legacy variables (remove these):",
        ])
        
        for legacy_var in self.analyzer.LEGACY_VAR_MAPPING.keys():
            env_lines.append(f"# {legacy_var}=")
        
        return "\n".join(env_lines)
    
    def _generate_docker_env(self, recommendation: MigrationRecommendation) -> str:
        """Generate Docker environment format."""
        docker_lines = [
            "# Docker Environment Variables for Resilience Configuration",
            f"# Preset: {recommendation.recommended_preset}",
            "",
            "environment:",
            f"  - RESILIENCE_PRESET={recommendation.recommended_preset}",
        ]
        
        if recommendation.custom_overrides:
            config_json = json.dumps(recommendation.custom_overrides, separators=(',', ':'))
            docker_lines.append(f"  - RESILIENCE_CUSTOM_CONFIG={config_json}")
        
        return "\n".join(docker_lines)


# Global migrator instance
migrator = ConfigurationMigrator()