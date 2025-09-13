#!/usr/bin/env python3
"""
Cache Configuration Validation Script

Provides validation, inspection, and recommendation capabilities for the
cache configuration preset system, following the resilience configuration 
validation pattern.

Usage:
    python validate_cache_config.py --list-presets
    python validate_cache_config.py --show-preset development
    python validate_cache_config.py --validate-current
    python validate_cache_config.py --validate-preset production
    python validate_cache_config.py --recommend-preset staging
    python validate_cache_config.py --quiet --list-presets
"""

import sys
import os
import argparse
import json
from typing import Dict, Any, Optional
from pathlib import Path

# Add the backend directory to the path so we can import our modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from app.infrastructure.cache.cache_presets import cache_preset_manager, CACHE_PRESETS, EnvironmentRecommendation
    from app.infrastructure.cache.cache_validator import cache_validator
    from app.core.config import Settings
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this from the backend directory and have installed dependencies.")
    sys.exit(1)


class CacheConfigValidator:
    """Main validator class for cache configuration operations."""
    
    def __init__(self, quiet: bool = False):
        """Initialize the validator."""
        self.quiet = quiet
        self.preset_manager = cache_preset_manager
        self.validator = cache_validator
    
    def list_presets(self) -> None:
        """List all available cache presets with descriptions."""
        if not self.quiet:
            print("\n" + "="*70)
            print(" AVAILABLE CACHE CONFIGURATION PRESETS")
            print("="*70)
        
        for preset_name in self.preset_manager.list_presets():
            preset = self.preset_manager.get_preset(preset_name)
            
            if not self.quiet:
                print(f"\n🗂️  {preset.name.upper()} PRESET ({preset_name})")
                print(f"   Description: {preset.description}")
                print(f"   Strategy: {preset.strategy.value}")
                print(f"   Default TTL: {preset.default_ttl}s ({preset.default_ttl//60} minutes)")
                print(f"   Max Connections: {preset.max_connections}")
                print(f"   Connection Timeout: {preset.connection_timeout}s")
                print(f"   Memory Cache Size: {preset.memory_cache_size}")
                print(f"   Compression Level: {preset.compression_level}")
                print(f"   AI Cache Enabled: {'✅ Yes' if preset.enable_ai_cache else '❌ No'}")
                
                if preset.ai_optimizations and preset.enable_ai_cache:
                    print(f"   AI Text Hash Threshold: {preset.ai_optimizations.get('text_hash_threshold', 'default')}")
                    op_ttls = preset.ai_optimizations.get('operation_ttls', {})
                    if op_ttls:
                        print(f"   AI Operation TTLs:")
                        for op, ttl in op_ttls.items():
                            print(f"     • {op}: {ttl}s ({ttl//60} minutes)")
                
                print(f"   Monitoring Enabled: {'✅ Yes' if preset.enable_monitoring else '❌ No'}")
                print(f"   Log Level: {preset.log_level}")
                print(f"   Suitable for: {', '.join(preset.environment_contexts)}")
            else:
                ai_status = "AI" if preset.enable_ai_cache else "Standard"
                print(f"{preset_name}: {preset.description} ({ai_status})")
        
        if not self.quiet:
            print("\n" + "="*70)
            print("💡 Usage: Set CACHE_PRESET environment variable to one of the above presets")
            print("   Example: export CACHE_PRESET=development")
            print("   Advanced: export CACHE_CUSTOM_CONFIG='{\"default_ttl\": 3600}'")
    
    def show_preset(self, preset_name: str) -> None:
        """Show detailed configuration for a specific preset."""
        try:
            preset = self.preset_manager.get_preset(preset_name)
            cache_config = preset.to_cache_config()
            config_dict = cache_config.to_dict()
            
            if not self.quiet:
                print(f"\n" + "="*70)
                print(f" DETAILED CONFIGURATION FOR '{preset_name.upper()}' PRESET")
                print("="*70)
                
                print(f"\n📋 PRESET METADATA")
                print(f"   Name: {preset.name}")
                print(f"   Description: {preset.description}")
                print(f"   Strategy: {preset.strategy.value}")
                print(f"   Environment Contexts: {', '.join(preset.environment_contexts)}")
                
                print(f"\n⚡ PERFORMANCE CONFIGURATION")
                print(f"   Default TTL: {config_dict.get('default_ttl', 'N/A')}s")
                print(f"   Max Connections: {config_dict.get('max_connections', 'N/A')}")
                print(f"   Connection Timeout: {config_dict.get('connection_timeout', 'N/A')}s")
                print(f"   Memory Cache Size: {config_dict.get('l1_cache_size', 'N/A')}")
                print(f"   Enable L1 Cache: {config_dict.get('enable_l1_cache', 'N/A')}")
                
                print(f"\n🗜️  COMPRESSION SETTINGS")
                print(f"   Compression Threshold: {config_dict.get('compression_threshold', 'N/A')} bytes")
                print(f"   Compression Level: {config_dict.get('compression_level', 'N/A')} (1-9)")
                
                print(f"\n🤖 AI FEATURES")
                print(f"   AI Cache Enabled: {'✅ Yes' if config_dict.get('enable_ai_cache', False) else '❌ No'}")
                
                if config_dict.get('enable_ai_cache', False):
                    print(f"   Text Hash Threshold: {config_dict.get('text_hash_threshold', 'N/A')}")
                    print(f"   Hash Algorithm: {config_dict.get('hash_algorithm', 'N/A')}")
                    print(f"   Smart Promotion: {config_dict.get('enable_smart_promotion', 'N/A')}")
                    print(f"   Max Text Length: {config_dict.get('max_text_length', 'N/A')}")
                    
                    op_ttls = config_dict.get('operation_ttls', {})
                    if op_ttls:
                        print(f"   Operation-specific TTLs:")
                        for operation, ttl in op_ttls.items():
                            print(f"     • {operation}: {ttl}s ({ttl//60} minutes)")
                    
                    text_tiers = config_dict.get('text_size_tiers', {})
                    if text_tiers:
                        print(f"   Text Size Tiers:")
                        for tier, size in text_tiers.items():
                            print(f"     • {tier}: {size} characters")
                
                print(f"\n📊 MONITORING")
                print(f"   Monitoring Enabled: {'✅ Yes' if config_dict.get('enable_monitoring', False) else '❌ No'}")
                print(f"   Log Level: {config_dict.get('log_level', 'N/A')}")
                
                print(f"\n🔧 FULL CONFIGURATION DICTIONARY")
                print("   (Use this for CACHE_CUSTOM_CONFIG if needed)")
                print("   " + "-"*66)
                print(json.dumps(config_dict, indent=4))
                
            else:
                print(json.dumps(config_dict, indent=2))
                
        except ValueError as e:
            print(f"❌ Error: {e}")
            return
        except Exception as e:
            print(f"❌ Unexpected error showing preset '{preset_name}': {e}")
            return
    
    def validate_preset(self, preset_name: str) -> None:
        """Validate a specific preset configuration."""
        try:
            preset = self.preset_manager.get_preset(preset_name)
            
            if not self.quiet:
                print(f"\n🔍 Validating '{preset_name}' preset configuration...")
                print("-" * 50)
            
            # Validate the preset
            is_valid = self.preset_manager.validate_preset(preset)
            
            if is_valid:
                if not self.quiet:
                    print(f"✅ Preset '{preset_name}' is valid!")
                    
                    # Show configuration summary
                    cache_config = preset.to_cache_config()
                    validation_result = cache_config.validate()
                    
                    if validation_result.warnings:
                        print(f"\n⚠️  Configuration warnings:")
                        for warning in validation_result.warnings:
                            print(f"   • {warning}")
                    
                    if validation_result.info:
                        print(f"\n💡 Configuration info:")
                        for info in validation_result.info:
                            print(f"   • {info}")
                else:
                    print(f"{preset_name}: VALID")
            else:
                print(f"❌ Preset '{preset_name}' has validation errors!")
                
        except ValueError as e:
            print(f"❌ Error: {e}")
            return
        except Exception as e:
            print(f"❌ Unexpected error validating preset '{preset_name}': {e}")
            return
    
    def validate_current(self) -> None:
        """Validate the current cache configuration from environment."""
        if not self.quiet:
            print(f"\n🔍 Validating current cache configuration...")
            print("-" * 50)
        
        try:
            # Load settings from current environment
            settings = Settings()
            
            cache_preset = getattr(settings, 'cache_preset', 'development')
            if not self.quiet:
                print(f"Current CACHE_PRESET: {cache_preset}")
            
            # Check for override environment variables
            overrides = []
            if os.getenv('CACHE_REDIS_URL'):
                overrides.append(f"CACHE_REDIS_URL={os.getenv('CACHE_REDIS_URL')}")
            if os.getenv('ENABLE_AI_CACHE'):
                overrides.append(f"ENABLE_AI_CACHE={os.getenv('ENABLE_AI_CACHE')}")
            if os.getenv('CACHE_CUSTOM_CONFIG'):
                overrides.append("CACHE_CUSTOM_CONFIG=<set>")
            
            if overrides and not self.quiet:
                print(f"Environment overrides detected:")
                for override in overrides:
                    print(f"   • {override}")
            
            # Get the actual configuration that would be used
            cache_config = settings.get_cache_config()
            validation_result = cache_config.validate()
            
            if validation_result.is_valid:
                if not self.quiet:
                    print(f"✅ Current cache configuration is valid!")
                    
                    # Show some key settings
                    config_dict = cache_config.to_dict()
                    print(f"\nKey Configuration Values:")
                    print(f"   • Strategy: {cache_config.strategy.value}")
                    print(f"   • Default TTL: {config_dict.get('default_ttl')}s")
                    print(f"   • AI Features: {'Enabled' if cache_config.enable_ai_cache else 'Disabled'}")
                    print(f"   • Redis URL: {config_dict.get('redis_url', 'Not set')}")
                    
                    if validation_result.warnings:
                        print(f"\n⚠️  Configuration warnings:")
                        for warning in validation_result.warnings:
                            print(f"   • {warning}")
                            
                    if validation_result.info:
                        print(f"\n💡 Configuration info:")
                        for info in validation_result.info:
                            print(f"   • {info}")
                else:
                    print("VALID")
            else:
                print(f"❌ Current cache configuration has errors!")
                for error in validation_result.errors:
                    print(f"   • {error}")
                    
        except Exception as e:
            print(f"❌ Error validating current configuration: {e}")
            return
    
    def recommend_preset(self, environment: Optional[str] = None) -> None:
        """Recommend appropriate preset for given or detected environment."""
        if not self.quiet:
            print(f"\n🎯 Recommending cache preset...")
            print("-" * 40)
        
        try:
            recommendation = self.preset_manager.recommend_preset_with_details(environment)
            
            if not self.quiet:
                print(f"Environment: {recommendation.environment_detected}")
                print(f"Recommended Preset: {recommendation.preset_name}")
                print(f"Confidence: {recommendation.confidence:.2%}")
                print(f"Reasoning: {recommendation.reasoning}")
                
                # Show preset details
                print(f"\n📋 RECOMMENDED PRESET DETAILS")
                preset = self.preset_manager.get_preset(recommendation.preset_name)
                print(f"   Description: {preset.description}")
                print(f"   Strategy: {preset.strategy.value}")
                print(f"   AI Features: {'✅ Enabled' if preset.enable_ai_cache else '❌ Disabled'}")
                print(f"   Default TTL: {preset.default_ttl}s ({preset.default_ttl//60} minutes)")
                
                print(f"\n💡 To use this preset:")
                print(f"   export CACHE_PRESET={recommendation.preset_name}")
                
                if recommendation.confidence < 0.8:
                    print(f"\n⚠️  Low confidence recommendation. Consider:")
                    print(f"   • Manually specify environment with --environment flag")
                    print(f"   • Review available presets with --list-presets")
                    print(f"   • Use CACHE_CUSTOM_CONFIG for fine-tuning")
            else:
                print(f"{recommendation.preset_name}")
                
        except Exception as e:
            print(f"❌ Error getting preset recommendation: {e}")
            return


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Cache Configuration Validation and Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-presets                    # List all available presets
  %(prog)s --show-preset development         # Show detailed preset config
  %(prog)s --validate-current                # Validate current environment
  %(prog)s --validate-preset production      # Validate specific preset
  %(prog)s --recommend-preset staging        # Get preset recommendation
  %(prog)s --quiet --list-presets            # Machine-readable output
        """
    )
    
    parser.add_argument(
        '--list-presets',
        action='store_true',
        help='List all available cache presets'
    )
    
    parser.add_argument(
        '--show-preset',
        metavar='PRESET_NAME',
        help='Show detailed configuration for a specific preset'
    )
    
    parser.add_argument(
        '--validate-current',
        action='store_true',
        help='Validate the current cache configuration from environment'
    )
    
    parser.add_argument(
        '--validate-preset',
        metavar='PRESET_NAME',
        help='Validate a specific preset configuration'
    )
    
    parser.add_argument(
        '--recommend-preset',
        nargs='?',
        const='',
        metavar='ENVIRONMENT',
        help='Recommend appropriate preset for environment (auto-detects if not specified)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode - minimal output suitable for scripts'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    action_count = sum([
        args.list_presets,
        bool(args.show_preset),
        args.validate_current,
        bool(args.validate_preset),
        args.recommend_preset is not None
    ])
    
    if action_count == 0:
        parser.print_help()
        sys.exit(1)
    
    if action_count > 1:
        print("❌ Error: Please specify only one action at a time")
        sys.exit(1)
    
    # Initialize validator
    validator = CacheConfigValidator(quiet=args.quiet)
    
    # Execute requested action
    try:
        if args.list_presets:
            validator.list_presets()
        elif args.show_preset:
            validator.show_preset(args.show_preset)
        elif args.validate_current:
            validator.validate_current()
        elif args.validate_preset:
            validator.validate_preset(args.validate_preset)
        elif args.recommend_preset is not None:
            env = args.recommend_preset if args.recommend_preset else None
            validator.recommend_preset(env)
            
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