#!/usr/bin/env python3
"""
CLI tool for migrating legacy cache configuration to preset-based system.

This script analyzes your current environment variables and provides
recommendations for migrating from individual CACHE_* variables to the 
simplified preset-based configuration system.

Supports migration from Phase 3 cache configuration (28+ variables) to 
Phase 4 preset system (1 primary + 2-3 overrides).
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

# Add the backend app directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from app.infrastructure.cache.cache_presets import cache_preset_manager, CACHE_PRESETS
    from app.infrastructure.cache.cache_validator import cache_validator
except ImportError as e:
    print(f"Error importing cache utilities: {e}")
    print("Make sure you're running this script from the backend directory")
    sys.exit(1)


@dataclass
class MigrationRecommendation:
    """Recommendation for migrating to preset system."""
    recommended_preset: str
    confidence: float
    overrides_needed: Dict[str, Any]
    custom_config_needed: Dict[str, Any]
    reasoning: str
    legacy_vars_found: List[str]
    complexity_reduction: str


class CacheConfigMigrator:
    """Migrates legacy cache configuration to preset system."""
    
    # Legacy environment variables that should be migrated
    LEGACY_CACHE_VARS = {
        'CACHE_REDIS_URL': 'redis_url',
        'CACHE_REDIS_PASSWORD': 'redis_password', 
        'CACHE_USE_TLS': 'use_tls',
        'CACHE_TLS_CERT_PATH': 'tls_cert_path',
        'CACHE_TLS_KEY_PATH': 'tls_key_path',
        'CACHE_DEFAULT_TTL': 'default_ttl',
        'CACHE_MEMORY_SIZE': 'memory_cache_size',
        'CACHE_MEMORY_CACHE_SIZE': 'memory_cache_size',
        'CACHE_COMPRESSION_THRESHOLD': 'compression_threshold',
        'CACHE_COMPRESSION_LEVEL': 'compression_level',
        'CACHE_ENVIRONMENT': 'environment',
        'ENABLE_AI_CACHE': 'enable_ai_cache',
        'CACHE_ENABLE_AI_FEATURES': 'enable_ai_cache',
        'CACHE_TEXT_HASH_THRESHOLD': 'text_hash_threshold',
        'CACHE_HASH_ALGORITHM': 'hash_algorithm',
        'CACHE_MAX_TEXT_LENGTH': 'max_text_length',
        'CACHE_ENABLE_SMART_PROMOTION': 'enable_smart_promotion',
        'CACHE_ENABLE_MONITORING': 'enable_monitoring',
        'CACHE_LOG_LEVEL': 'log_level',
        'CACHE_MAX_CONNECTIONS': 'max_connections',
        'CACHE_CONNECTION_TIMEOUT': 'connection_timeout',
        
        # AI-specific operation TTLs
        'CACHE_SUMMARIZE_TTL': 'operation_ttls.summarize',
        'CACHE_SENTIMENT_TTL': 'operation_ttls.sentiment',
        'CACHE_KEY_POINTS_TTL': 'operation_ttls.key_points',
        'CACHE_QUESTIONS_TTL': 'operation_ttls.questions',
        'CACHE_QA_TTL': 'operation_ttls.qa',
        
        # Text size tiers
        'CACHE_TEXT_SIZE_SMALL': 'text_size_tiers.small',
        'CACHE_TEXT_SIZE_MEDIUM': 'text_size_tiers.medium',
        'CACHE_TEXT_SIZE_LARGE': 'text_size_tiers.large',
    }
    
    def __init__(self):
        """Initialize the migrator."""
        self.preset_manager = cache_preset_manager
        self.validator = cache_validator
    
    def detect_legacy_configuration(self, env_vars: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Detect legacy cache configuration from environment variables.
        
        Args:
            env_vars: Environment variables dict (defaults to os.environ)
            
        Returns:
            Dictionary of detected legacy configuration
        """
        if env_vars is None:
            env_vars = dict(os.environ)
        
        legacy_config = {}
        found_vars = []
        
        for env_var, config_key in self.LEGACY_CACHE_VARS.items():
            if env_var in env_vars:
                value = env_vars[env_var]
                found_vars.append(env_var)
                
                # Handle nested keys (like operation_ttls.summarize)
                if '.' in config_key:
                    main_key, sub_key = config_key.split('.', 1)
                    if main_key not in legacy_config:
                        legacy_config[main_key] = {}
                    # Convert numeric values
                    try:
                        legacy_config[main_key][sub_key] = int(value)
                    except ValueError:
                        legacy_config[main_key][sub_key] = value
                else:
                    # Convert boolean values
                    if value.lower() in ('true', '1', 'yes'):
                        legacy_config[config_key] = True
                    elif value.lower() in ('false', '0', 'no'):
                        legacy_config[config_key] = False
                    else:
                        # Try to convert to int, fall back to string
                        try:
                            legacy_config[config_key] = int(value)
                        except ValueError:
                            legacy_config[config_key] = value
        
        legacy_config['_found_vars'] = found_vars
        return legacy_config
    
    def find_best_preset_match(self, legacy_config: Dict[str, Any]) -> MigrationRecommendation:
        """
        Find the best preset match for legacy configuration.
        
        Args:
            legacy_config: Detected legacy configuration
            
        Returns:
            Migration recommendation with preset and overrides
        """
        best_match = None
        best_score = 0
        best_preset_name = "development"  # Default fallback
        
        # Remove metadata from legacy config for analysis
        analysis_config = {k: v for k, v in legacy_config.items() if not k.startswith('_')}
        
        # Score each preset against the legacy configuration
        for preset_name in self.preset_manager.list_presets():
            preset = self.preset_manager.get_preset(preset_name)
            preset_config = preset.to_cache_config()
            
            score = self._calculate_preset_match_score(analysis_config, preset_config)
            
            if score > best_score:
                best_score = score
                best_match = preset
                best_preset_name = preset_name
        
        # Determine what overrides and custom config are needed
        overrides_needed = self._determine_overrides(analysis_config, best_match.to_cache_config())
        custom_config_needed = self._determine_custom_config(analysis_config, best_match.to_cache_config(), overrides_needed)
        
        # Calculate confidence and reasoning
        confidence = min(best_score / 100, 1.0)  # Normalize to 0-1 range
        reasoning = self._generate_reasoning(best_preset_name, best_score, analysis_config)
        
        # Calculate complexity reduction
        vars_before = len(legacy_config.get('_found_vars', []))
        vars_after = 1 + len(overrides_needed) + (1 if custom_config_needed else 0)
        complexity_reduction = f"{vars_before} variables → {vars_after} variables ({vars_before - vars_after} fewer)"
        
        return MigrationRecommendation(
            recommended_preset=best_preset_name,
            confidence=confidence,
            overrides_needed=overrides_needed,
            custom_config_needed=custom_config_needed,
            reasoning=reasoning,
            legacy_vars_found=legacy_config.get('_found_vars', []),
            complexity_reduction=complexity_reduction
        )
    
    def _calculate_preset_match_score(self, legacy_config: Dict[str, Any], preset_config) -> int:
        """Calculate how well a preset matches the legacy configuration."""
        score = 50  # Base score
        
        # Check key parameters
        preset_dict = preset_config.to_dict()
        
        # TTL matching (high importance)
        legacy_ttl = legacy_config.get('default_ttl')
        if legacy_ttl:
            preset_ttl = preset_dict.get('default_ttl', 3600)
            if abs(legacy_ttl - preset_ttl) < preset_ttl * 0.2:  # Within 20%
                score += 20
            elif abs(legacy_ttl - preset_ttl) < preset_ttl * 0.5:  # Within 50%
                score += 10
        
        # AI features matching (high importance)
        legacy_ai = legacy_config.get('enable_ai_cache', False)
        preset_ai = preset_config.enable_ai_cache
        if legacy_ai == preset_ai:
            score += 25
        
        # Connection settings matching (medium importance)
        if 'max_connections' in legacy_config:
            legacy_conn = legacy_config['max_connections']
            preset_conn = preset_dict.get('max_connections', 10)
            if abs(legacy_conn - preset_conn) < 5:
                score += 10
        
        # Memory cache size matching (medium importance)
        if 'memory_cache_size' in legacy_config:
            legacy_mem = legacy_config['memory_cache_size']
            preset_mem = preset_dict.get('l1_cache_size', 100)
            if abs(legacy_mem - preset_mem) < preset_mem * 0.3:
                score += 10
        
        # Environment context matching (if available)
        legacy_env = legacy_config.get('environment', '').lower()
        if legacy_env:
            preset = self.preset_manager.get_preset(preset_config.strategy.value if hasattr(preset_config, 'strategy') else 'balanced')
            if legacy_env in [ctx.lower() for ctx in getattr(preset, 'environment_contexts', [])]:
                score += 15
        
        return score
    
    def _determine_overrides(self, legacy_config: Dict[str, Any], preset_config) -> Dict[str, Any]:
        """Determine which environment variable overrides are needed."""
        overrides = {}
        preset_dict = preset_config.to_dict()
        
        # Redis URL override (always preserve if set)
        if 'redis_url' in legacy_config:
            overrides['CACHE_REDIS_URL'] = legacy_config['redis_url']
        
        # AI cache override (if different from preset)
        legacy_ai = legacy_config.get('enable_ai_cache', False)
        if legacy_ai != preset_config.enable_ai_cache:
            overrides['ENABLE_AI_CACHE'] = str(legacy_ai).lower()
        
        return overrides
    
    def _determine_custom_config(self, legacy_config: Dict[str, Any], preset_config, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Determine what custom JSON configuration is needed."""
        custom_config = {}
        preset_dict = preset_config.to_dict()
        
        # Check for significant differences that need custom config
        fields_to_check = [
            ('default_ttl', 'default_ttl'),
            ('max_connections', 'max_connections'), 
            ('connection_timeout', 'connection_timeout'),
            ('memory_cache_size', 'l1_cache_size'),
            ('compression_threshold', 'compression_threshold'),
            ('compression_level', 'compression_level'),
            ('text_hash_threshold', 'text_hash_threshold'),
        ]
        
        for legacy_key, preset_key in fields_to_check:
            if legacy_key in legacy_config:
                legacy_value = legacy_config[legacy_key]
                preset_value = preset_dict.get(preset_key)
                
                # Only add to custom config if significantly different
                if preset_value is not None and legacy_value != preset_value:
                    # For TTL, only include if difference is > 20%
                    if legacy_key == 'default_ttl':
                        if abs(legacy_value - preset_value) > preset_value * 0.2:
                            custom_config[legacy_key] = legacy_value
                    else:
                        custom_config[legacy_key] = legacy_value
        
        # Handle nested configurations (operation_ttls, text_size_tiers)
        if 'operation_ttls' in legacy_config and legacy_config['operation_ttls']:
            custom_config['operation_ttls'] = legacy_config['operation_ttls']
        
        if 'text_size_tiers' in legacy_config and legacy_config['text_size_tiers']:
            custom_config['text_size_tiers'] = legacy_config['text_size_tiers']
        
        return custom_config
    
    def _generate_reasoning(self, preset_name: str, score: int, legacy_config: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for the recommendation."""
        reasons = []
        
        if legacy_config.get('enable_ai_cache', False):
            if 'ai' in preset_name:
                reasons.append("AI features detected - using AI-optimized preset")
            else:
                reasons.append("AI features detected but preset doesn't include AI optimization")
        
        env_context = legacy_config.get('environment', '').lower()
        if env_context and env_context in preset_name.lower():
            reasons.append(f"Environment '{env_context}' matches preset context")
        
        ttl = legacy_config.get('default_ttl')
        if ttl:
            if ttl < 1800:  # 30 minutes
                reasons.append("Short TTL suggests development/testing usage")
            elif ttl > 7200:  # 2 hours
                reasons.append("Long TTL suggests production usage")
        
        if score > 80:
            reasons.append("High confidence match with preset defaults")
        elif score > 60:
            reasons.append("Good match with some customization needed")
        else:
            reasons.append("Partial match - consider manual preset selection")
        
        return "; ".join(reasons) if reasons else "Best available preset match"


def print_banner():
    """Print the CLI tool banner."""
    print("=" * 80)
    print("  Cache Configuration Migration Tool")
    print("  From 28+ environment variables to simple preset system")
    print("=" * 80)
    print()


def print_preset_info():
    """Print information about available presets."""
    print("Available Cache Presets:")
    print("-" * 60)
    
    for preset_name in cache_preset_manager.list_presets():
        preset = cache_preset_manager.get_preset(preset_name)
        ai_status = "🤖 AI-enabled" if preset.enable_ai_cache else "📝 Standard"
        
        print(f"  {preset.name.upper()} ({preset_name}) - {ai_status}")
        print(f"    {preset.description}")
        print(f"    • Default TTL: {preset.default_ttl}s ({preset.default_ttl//60} minutes)")
        print(f"    • Max connections: {preset.max_connections}")
        print(f"    • Strategy: {preset.strategy.value}")
        print(f"    • Environments: {', '.join(preset.environment_contexts)}")
        print()


def analyze_configuration(env_file: Optional[str] = None, quiet: bool = False) -> None:
    """Analyze current configuration and provide migration recommendations."""
    migrator = CacheConfigMigrator()
    
    if not quiet:
        print("Analyzing Current Cache Configuration...")
        print("-" * 50)
    
    # Load environment variables from file if specified
    env_vars = dict(os.environ)
    if env_file:
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            if not quiet:
                print(f"Loaded environment variables from: {env_file}")
        except ImportError:
            if not quiet:
                print("Warning: python-dotenv not available, using system environment only")
        except Exception as e:
            print(f"Error loading .env file: {e}")
            return
    
    # Detect legacy configuration
    legacy_config = migrator.detect_legacy_configuration(env_vars)
    
    if not legacy_config.get('_found_vars'):
        if not quiet:
            print("✅ No legacy cache configuration detected!")
            print("   You can start fresh with: CACHE_PRESET=development")
            print("   For AI applications, use: CACHE_PRESET=ai-development")
        else:
            print("NO_LEGACY_CONFIG")
        return
    
    if not quiet:
        print(f"📋 Found {len(legacy_config['_found_vars'])} legacy cache variables:")
        for var in sorted(legacy_config['_found_vars']):
            value = os.getenv(var, 'N/A')
            if 'password' in var.lower() or 'key' in var.lower():
                value = '***hidden***'
            print(f"   • {var}={value}")
    
    # Get migration recommendation
    recommendation = migrator.find_best_preset_match(legacy_config)
    
    if not quiet:
        print(f"\n🎯 MIGRATION RECOMMENDATION")
        print("-" * 40)
        print(f"Recommended Preset: {recommendation.recommended_preset}")
        print(f"Confidence: {recommendation.confidence:.1%}")
        print(f"Reasoning: {recommendation.reasoning}")
        print(f"Complexity Reduction: {recommendation.complexity_reduction}")
        
        print(f"\n🚀 MIGRATION STEPS")
        print("-" * 30)
        print("1. Set the cache preset:")
        print(f"   export CACHE_PRESET={recommendation.recommended_preset}")
        
        if recommendation.overrides_needed:
            print("\n2. Add essential overrides:")
            for key, value in recommendation.overrides_needed.items():
                print(f"   export {key}={value}")
        
        if recommendation.custom_config_needed:
            print("\n3. Add custom configuration (optional):")
            custom_json = json.dumps(recommendation.custom_config_needed, indent=4)
            print(f"   export CACHE_CUSTOM_CONFIG='{json.dumps(recommendation.custom_config_needed)}'")
            print(f"\n   Or in readable format:")
            for line in custom_json.split('\n'):
                print(f"   {line}")
        
        if not recommendation.overrides_needed and not recommendation.custom_config_needed:
            print("\n2. No additional configuration needed! ✨")
            print("   The preset handles everything automatically.")
        
        print(f"\n4. Remove old environment variables:")
        print("   # You can now remove these old variables:")
        for var in sorted(recommendation.legacy_vars_found):
            print(f"   # unset {var}")
        
        print(f"\n💡 VERIFICATION")
        print("-" * 20)
        print("After migration, verify with:")
        print("python scripts/validate_cache_config.py --validate-current")
    else:
        # Machine-readable output
        result = {
            "legacy_vars_found": len(recommendation.legacy_vars_found),
            "recommended_preset": recommendation.recommended_preset,
            "confidence": recommendation.confidence,
            "overrides_needed": recommendation.overrides_needed,
            "custom_config_needed": recommendation.custom_config_needed,
            "complexity_reduction": recommendation.complexity_reduction
        }
        print(json.dumps(result, indent=2))


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Cache Configuration Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --analyze                         # Analyze current environment
  %(prog)s --analyze --env-file .env         # Analyze specific .env file
  %(prog)s --list-presets                    # Show available presets
  %(prog)s --quiet --analyze                 # Machine-readable output
        """
    )
    
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze current configuration and provide migration recommendations'
    )
    
    parser.add_argument(
        '--list-presets',
        action='store_true',
        help='List all available cache presets'
    )
    
    parser.add_argument(
        '--env-file',
        metavar='FILE',
        help='Load environment variables from specific .env file'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode - minimal output suitable for scripts'
    )
    
    args = parser.parse_args()
    
    # Show help if no arguments
    if not any([args.analyze, args.list_presets]):
        parser.print_help()
        sys.exit(1)
    
    try:
        if not args.quiet:
            print_banner()
        
        if args.list_presets:
            print_preset_info()
            
        if args.analyze:
            analyze_configuration(args.env_file, args.quiet)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()