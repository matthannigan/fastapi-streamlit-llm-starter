# Resilience API Endpoints.

  file_path: `backend/app/api/internal/resilience/__init__.py`

backend/app/api/internal/resilience/
├── __init__.py
├── models.py
├── health.py              # 6 endpoints - health/metrics
├── config_presets.py      # 6 endpoints - preset recommendations
├── config_templates.py    # 4 endpoints - template patterns
├── config_validation.py   # 7 endpoints - config validation functions
├── circuit_breakers.py    # 3 endpoints - CB management
├── monitoring.py          # 7 endpoints - analytics
└── performance.py         # 5 endpoints - benchmarking
