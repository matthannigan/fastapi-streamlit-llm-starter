#!/usr/bin/env python3
"""
Resilience Configuration Health Check Script

Lightweight health check for Docker containers to verify resilience configuration
is loaded correctly and functioning.

Usage:
    python health_check_resilience.py
    
Exit codes:
    0: Healthy - resilience configuration is valid and loaded
    1: Unhealthy - resilience configuration has issues
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_resilience_health():
    """
    Perform a quick health check of the resilience configuration.
    Returns True if healthy, False if unhealthy.
    """
    try:
        # Import required modules
        from app.config import Settings
        from app.resilience_presets import preset_manager
        from app.services.resilience import AIServiceResilience
        
        # Check 1: Can we load settings?
        settings = Settings()
        
        # Check 2: Is the preset valid?
        preset = preset_manager.get_preset(settings.resilience_preset)
        
        # Check 3: Can we create resilience configuration?
        resilience_config = settings.get_resilience_config()
        
        # Check 4: Can the resilience service initialize?
        resilience_service = AIServiceResilience(settings=settings)
        
        # Check 5: Are operation configurations available?
        test_operations = ["summarize", "sentiment", "qa"]
        for operation in test_operations:
            config = resilience_service.get_operation_config(operation)
            if config is None:
                return False
        
        return True
        
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        return False

def main():
    """Main entry point for health check."""
    if check_resilience_health():
        print("Resilience configuration: HEALTHY")
        sys.exit(0)
    else:
        print("Resilience configuration: UNHEALTHY")
        sys.exit(1)

if __name__ == "__main__":
    main() 