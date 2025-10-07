"""
Resilience API Endpoints.

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
"""

from .config_presets import router as resilience_config_presets_router
from .config_templates import router as resilience_config_templates_router
from .config_validation import router as resilience_config_validation_router
from .circuit_breakers import router as resilience_circuit_breakers_router
from .health import main_router as resilience_health_router, config_router as resilience_config_router
from .monitoring import router as resilience_monitoring_router
from .performance import router as resilience_performance_router

__all__ = ['resilience_circuit_breakers_router', 'resilience_config_presets_router', 'resilience_config_router', 'resilience_config_templates_router', 'resilience_config_validation_router', 'resilience_health_router', 'resilience_monitoring_router', 'resilience_performance_router']
