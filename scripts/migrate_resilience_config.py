#!/usr/bin/env python3
"""
Resilience Configuration Migration Script

This script helps migrate from legacy resilience configuration (47+ environment variables)
to the simplified preset-based configuration system.

Usage:
    python scripts/migrate_resilience_config.py [options]

Options:
    --analyze         Analyze current configuration and suggest preset
    --migrate         Generate migration commands
    --dry-run         Show what would be done without making changes
    --output FILE     Save migration to file
    --help            Show this help message
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Legacy environment variables mapping
LEGACY_CONFIG_MAPPING = {
    # Core settings
    "RETRY_MAX_ATTEMPTS": "retry_attempts",
    "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "circuit_breaker_threshold", 
    "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "recovery_timeout",
    "DEFAULT_RESILIENCE_STRATEGY": "default_strategy",
    
    # Retry configuration
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

# Preset definitions for comparison
PRESET_CONFIGS = {
    "simple": {
        "retry_attempts": 3,
        "circuit_breaker_threshold": 5,
        "recovery_timeout": 60,
        "default_strategy": "balanced",
        "operation_overrides": {}
    },
    "development": {
        "retry_attempts": 2,
        "circuit_breaker_threshold": 3,
        "recovery_timeout": 30,
        "default_strategy": "aggressive",
        "operation_overrides": {
            "sentiment": "aggressive",
            "qa": "balanced"
        }
    },
    "production": {
        "retry_attempts": 5,
        "circuit_breaker_threshold": 10,
        "recovery_timeout": 120,
        "default_strategy": "conservative",
        "operation_overrides": {
            "qa": "critical",
            "sentiment": "aggressive", 
            "summarize": "conservative",
            "key_points": "balanced",
            "questions": "balanced"
        }
    }
}


class ResilienceConfigMigrator:
    """Migrate legacy resilience configuration to preset-based system."""
    
    def __init__(self):
        self.legacy_config = self._detect_legacy_config()
        self.normalized_config = self._normalize_legacy_config()
    
    def _detect_legacy_config(self) -> Dict[str, str]:
        """Detect legacy configuration from environment variables."""
        legacy_config = {}
        
        for legacy_var, _ in LEGACY_CONFIG_MAPPING.items():
            value = os.getenv(legacy_var)
            if value is not None:
                legacy_config[legacy_var] = value
        
        return legacy_config
    
    def _normalize_legacy_config(self) -> Dict[str, any]:
        """Convert legacy environment variables to normalized configuration."""
        normalized = {}
        operation_overrides = {}
        
        for legacy_var, value in self.legacy_config.items():
            mapped_key = LEGACY_CONFIG_MAPPING.get(legacy_var)
            if not mapped_key:
                continue
            
            # Handle operation-specific overrides
            if mapped_key.startswith("operation_overrides."):
                operation = mapped_key.split(".", 1)[1]
                operation_overrides[operation] = value
            else:
                # Convert types
                if mapped_key in ["retry_attempts", "circuit_breaker_threshold", "recovery_timeout", "max_delay_seconds"]:
                    normalized[mapped_key] = int(value)
                elif mapped_key in ["exponential_multiplier", "exponential_min", "exponential_max", "jitter_max"]:
                    normalized[mapped_key] = float(value)
                elif mapped_key == "jitter_enabled":
                    normalized[mapped_key] = value.lower() in ("true", "1", "yes")
                else:
                    normalized[mapped_key] = value
        
        if operation_overrides:
            normalized["operation_overrides"] = operation_overrides
        
        return normalized
    
    def analyze_current_config(self) -> Dict[str, any]:
        """Analyze current configuration and provide recommendations."""
        if not self.legacy_config:
            return {
                "has_legacy_config": False,
                "current_preset": os.getenv("RESILIENCE_PRESET", "simple"),
                "recommendation": "No legacy configuration detected. Current preset-based configuration is recommended.",
                "suggested_preset": os.getenv("RESILIENCE_PRESET", "simple")
            }
        
        # Calculate similarity scores with presets
        scores = {}
        for preset_name, preset_config in PRESET_CONFIGS.items():
            score = self._calculate_similarity_score(self.normalized_config, preset_config)
            scores[preset_name] = score
        
        # Find best matching preset
        best_preset = max(scores, key=scores.get)
        best_score = scores[best_preset]
        
        return {
            "has_legacy_config": True,
            "legacy_variables_count": len(self.legacy_config),
            "legacy_variables": list(self.legacy_config.keys()),
            "normalized_config": self.normalized_config,
            "preset_similarity_scores": scores,
            "suggested_preset": best_preset,
            "similarity_confidence": best_score,
            "recommendation": self._generate_recommendation(best_preset, best_score)
        }
    
    def _calculate_similarity_score(self, config: Dict, preset: Dict) -> float:
        """Calculate similarity score between config and preset (0.0 to 1.0)."""
        score = 0.0
        total_weight = 0.0
        
        # Weight important parameters more heavily
        weights = {
            "retry_attempts": 3.0,
            "circuit_breaker_threshold": 2.0,
            "recovery_timeout": 1.5,
            "default_strategy": 2.5,
            "operation_overrides": 2.0
        }
        
        for key, weight in weights.items():
            total_weight += weight
            
            if key == "operation_overrides":
                # Compare operation overrides
                config_overrides = config.get(key, {})
                preset_overrides = preset.get(key, {})
                
                if not config_overrides and not preset_overrides:
                    score += weight  # Both empty
                elif config_overrides == preset_overrides:
                    score += weight  # Exact match
                else:
                    # Partial match based on common operations
                    common_ops = set(config_overrides.keys()) & set(preset_overrides.keys())
                    matching_ops = sum(1 for op in common_ops 
                                     if config_overrides[op] == preset_overrides[op])
                    if common_ops:
                        score += weight * (matching_ops / len(common_ops))
            else:
                if config.get(key) == preset.get(key):
                    score += weight
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _generate_recommendation(self, best_preset: str, confidence: float) -> str:
        """Generate migration recommendation based on analysis."""
        if confidence >= 0.8:
            return f"Strong match with '{best_preset}' preset. Migration recommended."
        elif confidence >= 0.6:
            return f"Good match with '{best_preset}' preset. Consider migration with minor customization."
        elif confidence >= 0.4:
            return f"Partial match with '{best_preset}' preset. Custom configuration may be better."
        else:
            return "No close preset match. Consider using custom configuration."
    
    def generate_migration_commands(self, target_preset: Optional[str] = None) -> List[str]:
        """Generate shell commands for migration."""
        analysis = self.analyze_current_config()
        
        if not analysis["has_legacy_config"]:
            return ["# No legacy configuration detected - no migration needed"]
        
        commands = []
        commands.append("#!/bin/bash")
        commands.append("# Resilience Configuration Migration")
        commands.append("# Generated by migrate_resilience_config.py")
        commands.append("")
        
        # Backup current configuration
        commands.append("# 1. Backup current configuration")
        commands.append("echo '# Legacy configuration backup' > .env.resilience.backup")
        for var in analysis["legacy_variables"]:
            commands.append(f"echo '{var}='\\$'{var}' >> .env.resilience.backup")
        commands.append("")
        
        # Choose target preset
        if not target_preset:
            target_preset = analysis["suggested_preset"]
        
        preset_config = PRESET_CONFIGS[target_preset]
        similarity = self._calculate_similarity_score(self.normalized_config, preset_config)
        
        commands.append(f"# 2. Set new preset configuration")
        commands.append(f"export RESILIENCE_PRESET={target_preset}")
        commands.append("")
        
        # Check if custom configuration is needed
        if similarity < 0.8:
            commands.append("# 3. Custom configuration needed for full compatibility")
            custom_config = self._generate_custom_config(target_preset)
            if custom_config:
                config_json = json.dumps(custom_config, separators=(',', ':'))
                commands.append(f"export RESILIENCE_CUSTOM_CONFIG='{config_json}'")
                commands.append("")
        
        # Remove legacy variables
        commands.append("# 4. Remove legacy configuration variables")
        for var in analysis["legacy_variables"]:
            commands.append(f"unset {var}")
        commands.append("")
        
        # Validation
        commands.append("# 5. Validate new configuration")
        commands.append("echo 'Testing new configuration...'")
        commands.append("curl -s http://localhost:8000/resilience/config | jq .")
        commands.append("")
        commands.append("echo 'Migration complete!'")
        commands.append("echo 'Restart your application to apply new configuration.'")
        
        return commands
    
    def _generate_custom_config(self, base_preset: str) -> Dict[str, any]:
        """Generate custom configuration for differences from preset."""
        preset_config = PRESET_CONFIGS[base_preset]
        custom_config = {}
        
        # Find differences that need custom configuration
        for key, value in self.normalized_config.items():
            if key == "operation_overrides":
                # Handle operation overrides
                current_overrides = value
                preset_overrides = preset_config.get("operation_overrides", {})
                
                # Only include overrides that differ from preset
                different_overrides = {}
                for op, strategy in current_overrides.items():
                    if preset_overrides.get(op) != strategy:
                        different_overrides[op] = strategy
                
                if different_overrides:
                    custom_config["operation_overrides"] = different_overrides
            else:
                if preset_config.get(key) != value:
                    custom_config[key] = value
        
        return custom_config


def main():
    """Main migration script entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate legacy resilience configuration to preset-based system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--analyze", action="store_true",
                       help="Analyze current configuration and suggest preset")
    parser.add_argument("--migrate", action="store_true", 
                       help="Generate migration commands")
    parser.add_argument("--preset", choices=["simple", "development", "production"],
                       help="Target preset for migration")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without making changes")
    parser.add_argument("--output", metavar="FILE",
                       help="Save migration commands to file")
    
    args = parser.parse_args()
    
    if not any([args.analyze, args.migrate]):
        parser.print_help()
        return
    
    migrator = ResilienceConfigMigrator()
    
    if args.analyze:
        print("=== Resilience Configuration Analysis ===")
        analysis = migrator.analyze_current_config()
        
        if not analysis["has_legacy_config"]:
            print("✅ No legacy configuration detected.")
            print(f"Current preset: {analysis['current_preset']}")
            print("No migration needed.")
            return
        
        print(f"📊 Legacy variables detected: {analysis['legacy_variables_count']}")
        print(f"Variables: {', '.join(analysis['legacy_variables'])}")
        print()
        
        print("Preset similarity scores:")
        for preset, score in analysis["preset_similarity_scores"].items():
            emoji = "🎯" if preset == analysis["suggested_preset"] else "📋"
            print(f"  {emoji} {preset}: {score:.2f}")
        
        print()
        print(f"🎯 Recommended preset: {analysis['suggested_preset']}")
        print(f"📝 Recommendation: {analysis['recommendation']}")
        
        if analysis["similarity_confidence"] < 0.8:
            print("⚠️  Custom configuration may be needed for full compatibility.")
    
    if args.migrate:
        print("=== Generating Migration Commands ===")
        commands = migrator.generate_migration_commands(args.preset)
        
        migration_script = "\n".join(commands)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(migration_script)
            print(f"Migration script saved to: {args.output}")
            if not args.dry_run:
                os.chmod(args.output, 0o755)  # Make executable
        else:
            print(migration_script)
        
        if args.dry_run:
            print("\n🔍 DRY RUN: Commands shown above would be executed.")
        else:
            print("\n✅ Migration commands generated.")
            print("Review the commands above and execute them when ready.")


if __name__ == "__main__":
    main()