#!/usr/bin/env python3
"""
CLI tool for migrating legacy resilience configuration to preset-based system.

This script analyzes your current environment variables and provides
recommendations for migrating to the simplified preset-based configuration.
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Optional

# Add the backend app directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from app.migration_utils import migrator, MigrationConfidence
    from app.resilience_presets import PRESETS
except ImportError as e:
    print(f"Error importing migration utilities: {e}")
    print("Make sure you're running this script from the backend directory")
    sys.exit(1)


def print_banner():
    """Print the CLI tool banner."""
    print("=" * 70)
    print("  Resilience Configuration Migration Tool")
    print("  From 47+ environment variables to simple presets")
    print("=" * 70)
    print()


def print_preset_info():
    """Print information about available presets."""
    print("Available Presets:")
    print("-" * 50)
    
    for preset_name, preset in PRESETS.items():
        print(f"  {preset.name.upper()} ({preset_name})")
        print(f"    {preset.description}")
        print(f"    • Retry attempts: {preset.retry_attempts}")
        print(f"    • Circuit breaker threshold: {preset.circuit_breaker_threshold}")
        print(f"    • Recovery timeout: {preset.recovery_timeout}s")
        print(f"    • Default strategy: {preset.default_strategy.value}")
        if preset.operation_overrides:
            print(f"    • Operation overrides: {len(preset.operation_overrides)} configured")
        print(f"    • Environments: {', '.join(preset.environment_contexts)}")
        print()


def analyze_configuration(env_file: Optional[str] = None) -> None:
    """Analyze current configuration and provide recommendations."""
    print("Analyzing Current Configuration...")
    print("-" * 40)
    
    # Load environment variables from file if specified
    env_vars = dict(os.environ)
    if env_file:
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"Loaded environment variables from: {env_file}")
        except ImportError:
            print("Warning: python-dotenv not available, using system environment only")
        except Exception as e:
            print(f"Error loading .env file: {e}")
            return
    
    # Detect legacy configuration
    legacy_config = migrator.analyzer.detect_legacy_configuration(env_vars)
    
    if not legacy_config:
        print("✅ No legacy resilience configuration detected!")
        print("   You can start fresh with: RESILIENCE_PRESET=simple")
        return
    
    print(f"📊 Found {len(legacy_config)} legacy configuration settings:")
    for key, value in legacy_config.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for subkey, subvalue in value.items():
                print(f"     {subkey}: {subvalue}")
        else:
            print(f"   {key}: {value}")
    print()
    
    # Get migration recommendation
    recommendation = migrator.analyzer.recommend_preset(legacy_config)
    
    # Display recommendation
    confidence_emoji = {
        MigrationConfidence.HIGH: "🎯",
        MigrationConfidence.MEDIUM: "👍",
        MigrationConfidence.LOW: "⚠️"
    }
    
    print("Migration Recommendation:")
    print("-" * 30)
    print(f"{confidence_emoji[recommendation.confidence]} Recommended Preset: {recommendation.recommended_preset.upper()}")
    print(f"   Confidence: {recommendation.confidence.value.upper()}")
    print(f"   Reasoning: {recommendation.reasoning}")
    print()
    
    # Display warnings
    if recommendation.warnings:
        print("⚠️  Warnings:")
        for warning in recommendation.warnings:
            print(f"   • {warning}")
        print()
    
    # Display custom overrides
    if recommendation.custom_overrides:
        print("🔧 Custom Overrides Needed:")
        print(json.dumps(recommendation.custom_overrides, indent=2))
        print()
    else:
        print("✅ No custom overrides needed - preset defaults are perfect!")
        print()


def generate_migration_files(output_dir: str, format_type: str = "all") -> None:
    """Generate migration files in specified format."""
    print(f"Generating Migration Files...")
    print("-" * 35)
    
    # Get recommendation
    recommendation = migrator.analyze_current_environment()
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    formats_to_generate = ["bash", "env", "docker"] if format_type == "all" else [format_type]
    
    for fmt in formats_to_generate:
        try:
            script_content = migrator.generate_migration_script(recommendation, fmt)
            
            # Determine file extension
            extensions = {"bash": ".sh", "env": ".env", "docker": ".yml"}
            extension = extensions.get(fmt, ".txt")
            
            file_path = output_path / f"migrate-to-{recommendation.recommended_preset}{extension}"
            
            with open(file_path, 'w') as f:
                f.write(script_content)
            
            print(f"✅ Generated {fmt} migration file: {file_path}")
            
            # Make bash scripts executable
            if fmt == "bash":
                os.chmod(file_path, 0o755)
                
        except Exception as e:
            print(f"❌ Error generating {fmt} file: {e}")
    
    print()
    print("Migration Steps:")
    print("-" * 20)
    for i, step in enumerate(recommendation.migration_steps, 1):
        print(f"{i}. {step}")


def interactive_migration() -> None:
    """Interactive migration wizard."""
    print("Interactive Migration Wizard")
    print("-" * 35)
    print()
    
    # Step 1: Analyze current config
    print("Step 1: Analyzing your current configuration...")
    recommendation = migrator.analyze_current_environment()
    
    if not migrator.analyzer.detect_legacy_configuration():
        print("✅ No legacy configuration found. You're ready to use presets!")
        preset = input("Choose a preset (simple/development/production) [simple]: ").strip() or "simple"
        print(f"Set: RESILIENCE_PRESET={preset}")
        return
    
    print(f"Found legacy configuration. Recommended preset: {recommendation.recommended_preset}")
    print()
    
    # Step 2: Confirm preset choice
    print("Step 2: Choose your preset")
    print("Available options:")
    for name in PRESETS.keys():
        marker = " (recommended)" if name == recommendation.recommended_preset else ""
        print(f"  • {name}{marker}")
    
    chosen_preset = input(f"Choose preset [{recommendation.recommended_preset}]: ").strip()
    if not chosen_preset:
        chosen_preset = recommendation.recommended_preset
    
    if chosen_preset not in PRESETS:
        print(f"Invalid preset: {chosen_preset}")
        return
    
    print()
    
    # Step 3: Handle custom overrides
    if recommendation.custom_overrides:
        print("Step 3: Custom configuration overrides")
        print("Your legacy config has custom values that don't match the preset defaults:")
        print(json.dumps(recommendation.custom_overrides, indent=2))
        print()
        
        use_overrides = input("Include these custom overrides? [y/N]: ").strip().lower()
        if use_overrides in ('y', 'yes'):
            custom_config = json.dumps(recommendation.custom_overrides)
            print(f"Set: RESILIENCE_CUSTOM_CONFIG='{custom_config}'")
        else:
            print("Using preset defaults only")
    else:
        print("Step 3: No custom overrides needed ✅")
    
    print()
    
    # Step 4: Generate migration commands
    print("Step 4: Migration commands")
    print("Run these commands to complete your migration:")
    print()
    print(f"export RESILIENCE_PRESET={chosen_preset}")
    
    if recommendation.custom_overrides and use_overrides in ('y', 'yes'):
        print(f"export RESILIENCE_CUSTOM_CONFIG='{json.dumps(recommendation.custom_overrides)}'")
    
    print("\n# Remove legacy variables:")
    for var in migrator.analyzer.LEGACY_VAR_MAPPING.keys():
        print(f"unset {var}")
    
    print("\n✅ Migration complete! Test your application with the new configuration.")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate legacy resilience configuration to preset-based system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current configuration
  python migrate-resilience-config.py analyze
  
  # Analyze specific .env file
  python migrate-resilience-config.py analyze --env-file .env.production
  
  # Generate migration files
  python migrate-resilience-config.py generate --output ./migration-files
  
  # Interactive migration wizard
  python migrate-resilience-config.py interactive
  
  # Show available presets
  python migrate-resilience-config.py presets
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze current configuration")
    analyze_parser.add_argument("--env-file", help="Path to .env file to analyze")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate migration files")
    generate_parser.add_argument("--output", "-o", default="./migration", 
                               help="Output directory for migration files")
    generate_parser.add_argument("--format", choices=["bash", "env", "docker", "all"], 
                               default="all", help="Migration file format")
    
    # Interactive command
    subparsers.add_parser("interactive", help="Interactive migration wizard")
    
    # Presets command
    subparsers.add_parser("presets", help="Show available presets")
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.command == "analyze":
        analyze_configuration(args.env_file)
    elif args.command == "generate":
        generate_migration_files(args.output, args.format)
    elif args.command == "interactive":
        interactive_migration()
    elif args.command == "presets":
        print_preset_info()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()