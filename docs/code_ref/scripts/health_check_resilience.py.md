---
sidebar_label: health_check_resilience
---

# Resilience Configuration Health Check Script

  file_path: `scripts/health_check_resilience.py`

Lightweight health check for Docker containers to verify resilience configuration
is loaded correctly and functioning.

## Usage

python health_check_resilience.py

## Exit codes

0: Healthy - resilience configuration is valid and loaded
1: Unhealthy - resilience configuration has issues
