"""Configuration module re-export for frontend.

This module re-exports the settings from app.config to make them available
at the frontend root level, allowing imports like 'from config import settings'
to work both in the app and in tests.
"""

from app.config import settings, Settings

__all__ = ['settings', 'Settings'] 