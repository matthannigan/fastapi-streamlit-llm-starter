"""
Core Application Imports

This file re-exports the application's central configuration object and
custom exception base classes, making them easily accessible from a single,
stable import path.

Example:
    from .core import settings
    from .core import ApplicationError (once moved)
"""

# This allows other modules to import settings directly from the core package
# during the transition, even though the file is still in its old location.
from ..config import settings, Settings

# Note: Once custom exceptions are moved to core/exceptions.py,
# you would add re-exports for them here as well.
# from .exceptions import ApplicationError, InfrastructureError
