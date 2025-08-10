#!/usr/bin/env python3
"""
Resilience Configuration Validation Script

Provides validation, inspection, and recommendation capabilities for the
resilience configuration preset system.

Usage:
    python validate_resilience_config.py --list-presets
    python validate_resilience_config.py --show-preset simple
    python validate_resilience_config.py --validate-current
    python validate_resilience_config.py --validate-preset production
    python validate_resilience_config.py --recommend-preset development
"""

import sys
import os
import argparse
import json
from typing import Dict, Any, Optional
from pathlib import Path

# Add the backend directory to the path so we can import our modules
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from app.resilience_presets import preset_manager, PRESETS, EnvironmentRecommendation
    from app.core.config import Settings
    from app.validation_schemas import config_validator
    from app.services.resilience import AIServiceResilience
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you're running this from the project root and have installed dependencies.")
    sys.exit(1)


class ResilienceConfigValidator:
    """Main validator class for resilience configuration operations."""
    
    def __init__(self, quiet: bool = False):
        """Initialize the validator."""
        self.quiet = quiet
        self.preset_manager = preset_manager
    
    def list_presets(self) -> None:
        """List all available presets with descriptions."""
        if not self.quiet:
            print("\n" + "="*60)
            print(" AVAILABLE RESILIENCE CONFIGURATION PRESETS")
            print("="*60)
        
        for preset_name in self.preset_manager.list_presets():
            preset = self.preset_manager.get_preset(preset_name)
            
            if not self.quiet:
                print(f"\n📋 {preset.name.upper()} PRESET")
                print(f"   Description: {preset.description}")
                print(f"   Retry Attempts: {preset.retry_attempts}")
                print(f"   Circuit Breaker Threshold: {preset.circuit_breaker_threshold}")
                print(f"   Recovery Timeout: {preset.recovery_timeout}s")
                print(f"   Default Strategy: {preset.default_strategy.value}")
                
                if preset.operation_overrides:
                    print(f"   Operation Overrides:")
                    for op, strategy in preset.operation_overrides.items():
                        print(f"     • {op}: {strategy.value}")
                else:
                    print(f"   Operation Overrides: None")
                
                print(f"   Suitable for: {', '.join(preset.environment_contexts)}")
            else:
                print(f"{preset_name}: {preset.description}")
        
        if not self.quiet:
            print("\n" + "="*60)
            print("💡 Usage: Set RESILIENCE_PRESET environment variable to one of the above presets")
            print("   Example: export RESILIENCE_PRESET=simple")
    
    def show_preset(self, preset_name: str) -> None:
        """Show detailed information about a specific preset."""
        try:
            preset = self.preset_manager.get_preset(preset_name)
            
            print(f"\n{'='*70}")
            print(f" {preset.name.upper()} PRESET CONFIGURATION")
            print(f"{'='*70}")
            print(f"\n📝 Description: {preset.description}")
            
            print(f"\n⚙️  BASIC CONFIGURATION:")
            print(f"   • Retry Attempts: {preset.retry_attempts}")
            print(f"   • Circuit Breaker Threshold: {preset.circuit_breaker_threshold} failures")
            print(f"   • Recovery Timeout: {preset.recovery_timeout} seconds")
            print(f"   • Default Strategy: {preset.default_strategy.value}")
            
            print(f"\n🎯 OPERATION-SPECIFIC STRATEGIES:")
            if preset.operation_overrides:
                for operation, strategy in preset.operation_overrides.items():
                    print(f"   • {operation.title()}: {strategy.value}")
            else:
                print(f"   • All operations use default strategy: {preset.default_strategy.value}")
            
            print(f"\n🌍 ENVIRONMENT CONTEXTS:")
            print(f"   • Recommended for: {', '.join(preset.environment_contexts)}")
            
            print(f"\n📊 EXPECTED BEHAVIOR:")
            self._describe_preset_behavior(preset)
            
            print(f"\n💻 USAGE:")
            print(f"   export RESILIENCE_PRESET={preset_name}")
            print(f"   # Or in docker-compose.yml:")
            print(f"   environment:")
            print(f"     - RESILIENCE_PRESET={preset_name}")
            
            print(f"\n{'='*70}")
            
        except ValueError as e:
            print(f"❌ Error: {e}")
            return
    
    def _describe_preset_behavior(self, preset) -> None:
        """Describe the expected behavior of a preset."""
        if preset.name == "Simple":
            print("   • Balanced approach suitable for most applications")
            print("   • Moderate retry attempts with reasonable timeouts")
            print("   • Good default choice for testing and staging")
        elif preset.name == "Development":
            print("   • Fast-fail approach optimized for development speed")
            print("   • Quick feedback with minimal delays")
            print("   • Ideal for local development and CI/CD pipelines")
        elif preset.name == "Production":
            print("   • High-reliability configuration for production workloads")
            print("   • More retries and longer timeouts for better stability")
            print("   • Operation-specific optimizations for different use cases")
    
    def validate_current_config(self) -> bool:
        """Validate the current resilience configuration."""
        try:
            settings = Settings()
            
            if not self.quiet:
                print(f"\n🔍 VALIDATING CURRENT RESILIENCE CONFIGURATION")
                print(f"{'='*50}")
                print(f"Current preset: {settings.resilience_preset}")
                if settings.resilience_custom_config:
                    print(f"Custom config: Yes")
                else:
                    print(f"Custom config: No")
            
            # Validate preset exists and is valid
            try:
                preset = self.preset_manager.get_preset(settings.resilience_preset)
                if not self.quiet:
                    print(f"✅ Preset '{settings.resilience_preset}' is valid")
            except ValueError as e:
                print(f"❌ Invalid preset: {e}")
                return False
            
            # Validate custom configuration if present
            if settings.resilience_custom_config:
                try:
                    custom_config = json.loads(settings.resilience_custom_config)
                    validation_result = config_validator.validate_configuration(custom_config)
                    
                    if validation_result.is_valid:
                        if not self.quiet:
                            print(f"✅ Custom configuration is valid")
                    else:
                        print(f"❌ Custom configuration validation errors:")
                        for error in validation_result.errors:
                            print(f"   • {error}")
                        return False
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON in custom configuration: {e}")
                    return False
            
            # Test that configuration can be loaded by resilience service
            try:
                resilience_config = settings.get_resilience_config()
                resilience_service = AIServiceResilience(settings=settings)
                
                if not self.quiet:
                    print(f"✅ Configuration successfully loaded by resilience service")
                    print(f"✅ All operation configurations initialized")
                
            except Exception as e:
                print(f"❌ Error loading configuration into resilience service: {e}")
                return False
            
            if not self.quiet:
                print(f"\n✅ CONFIGURATION VALIDATION PASSED")
                print(f"Your resilience configuration is valid and ready to use!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during configuration validation: {e}")
            return False
    
    def validate_preset(self, preset_name: str) -> bool:
        """Validate a specific preset configuration."""
        try:
            preset = self.preset_manager.get_preset(preset_name)
            
            if not self.quiet:
                print(f"\n🔍 VALIDATING PRESET: {preset_name.upper()}")
                print(f"{'='*40}")
            
            # Validate preset parameters
            validation_passed = True
            
            # Check retry attempts
            if preset.retry_attempts < 1 or preset.retry_attempts > 10:
                print(f"❌ Invalid retry_attempts: {preset.retry_attempts} (must be 1-10)")
                validation_passed = False
            elif not self.quiet:
                print(f"✅ Retry attempts: {preset.retry_attempts}")
            
            # Check circuit breaker threshold
            if preset.circuit_breaker_threshold < 1 or preset.circuit_breaker_threshold > 20:
                print(f"❌ Invalid circuit_breaker_threshold: {preset.circuit_breaker_threshold} (must be 1-20)")
                validation_passed = False
            elif not self.quiet:
                print(f"✅ Circuit breaker threshold: {preset.circuit_breaker_threshold}")
            
            # Check recovery timeout
            if preset.recovery_timeout < 10 or preset.recovery_timeout > 300:
                print(f"❌ Invalid recovery_timeout: {preset.recovery_timeout} (must be 10-300 seconds)")
                validation_passed = False
            elif not self.quiet:
                print(f"✅ Recovery timeout: {preset.recovery_timeout}s")
            
            # Test conversion to resilience config
            try:
                resilience_config = preset.to_resilience_config()
                if not self.quiet:
                    print(f"✅ Successfully converts to resilience configuration")
            except Exception as e:
                print(f"❌ Error converting to resilience configuration: {e}")
                validation_passed = False
            
            if validation_passed:
                if not self.quiet:
                    print(f"\n✅ PRESET VALIDATION PASSED")
                    print(f"Preset '{preset_name}' is valid and ready to use!")
            else:
                print(f"\n❌ PRESET VALIDATION FAILED")
                
            return validation_passed
            
        except ValueError as e:
            print(f"❌ Error: {e}")
            return False
    
    def recommend_preset(self, environment: str) -> None:
        """Recommend appropriate preset for given environment."""
        print(f"\n🎯 PRESET RECOMMENDATION FOR: {environment.upper()}")
        print(f"{'='*50}")
        
        try:
            recommendation = self.preset_manager.recommend_preset(environment)
            
            print(f"📋 Recommended Preset: {recommendation.preset_name.upper()}")
            print(f"🎯 Confidence: {recommendation.confidence:.0%}")
            print(f"💭 Reasoning: {recommendation.reasoning}")
            print(f"🌍 Environment Detected: {recommendation.environment_detected}")
            
            # Show the recommended preset details
            try:
                preset = self.preset_manager.get_preset(recommendation.preset_name)
                print(f"\n📊 PRESET CONFIGURATION:")
                print(f"   • Description: {preset.description}")
                print(f"   • Retry Attempts: {preset.retry_attempts}")
                print(f"   • Circuit Breaker Threshold: {preset.circuit_breaker_threshold}")
                print(f"   • Recovery Timeout: {preset.recovery_timeout}s")
                print(f"   • Default Strategy: {preset.default_strategy.value}")
                
                if preset.operation_overrides:
                    print(f"   • Operation Overrides:")
                    for op, strategy in preset.operation_overrides.items():
                        print(f"     - {op}: {strategy.value}")
            except ValueError:
                pass
            
            print(f"\n💻 TO USE THIS PRESET:")
            print(f"   export RESILIENCE_PRESET={recommendation.preset_name}")
            print(f"   # Or add to your .env file:")
            print(f"   echo 'RESILIENCE_PRESET={recommendation.preset_name}' >> .env")
            
        except Exception as e:
            print(f"❌ Error generating recommendation: {e}")
            
            # Provide fallback recommendations
            print(f"\n📋 FALLBACK RECOMMENDATIONS:")
            
            env_lower = environment.lower()
            if any(keyword in env_lower for keyword in ['dev', 'development', 'local']):
                print(f"   For development: RESILIENCE_PRESET=development")
            elif any(keyword in env_lower for keyword in ['prod', 'production']):
                print(f"   For production: RESILIENCE_PRESET=production")  
            else:
                print(f"   General purpose: RESILIENCE_PRESET=simple")


def main():
    """Main entry point for the validation script."""
    parser = argparse.ArgumentParser(
        description="Resilience Configuration Validation and Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-presets
  %(prog)s --show-preset simple
  %(prog)s --validate-current
  %(prog)s --validate-preset production
  %(prog)s --recommend-preset development
        """
    )
    
    parser.add_argument('--list-presets', action='store_true',
                       help='List all available presets')
    parser.add_argument('--show-preset', metavar='PRESET',
                       help='Show detailed information about a specific preset')
    parser.add_argument('--validate-current', action='store_true',
                       help='Validate the current resilience configuration')
    parser.add_argument('--validate-preset', metavar='PRESET',
                       help='Validate a specific preset')
    parser.add_argument('--recommend-preset', metavar='ENVIRONMENT',
                       help='Get preset recommendation for an environment')
    parser.add_argument('--quiet', action='store_true',
                       help='Reduce output verbosity')
    
    args = parser.parse_args()
    
    # Check if no arguments provided
    if not any([args.list_presets, args.show_preset, args.validate_current, 
                args.validate_preset, args.recommend_preset]):
        parser.print_help()
        return
    
    validator = ResilienceConfigValidator(quiet=args.quiet)
    
    try:
        if args.list_presets:
            validator.list_presets()
        
        if args.show_preset:
            validator.show_preset(args.show_preset)
        
        if args.validate_current:
            success = validator.validate_current_config()
            sys.exit(0 if success else 1)
        
        if args.validate_preset:
            success = validator.validate_preset(args.validate_preset)
            sys.exit(0 if success else 1)
        
        if args.recommend_preset:
            validator.recommend_preset(args.recommend_preset)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 