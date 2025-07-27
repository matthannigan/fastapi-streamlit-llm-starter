"""Shared components package for cross-application data models and utilities.

This package provides common data structures, models, and utilities that are shared
between the frontend and backend components of the AI text processing application.

Modules:
    models: Pydantic model exports for text processing operations
    sample_data: Standardized sample texts and example data for consistent testing
    text_processing: Core Pydantic models for AI text processing operations

Re-exported Components:
    All models and sample data functions are re-exported at package level for convenience.
"""

# Import and expose main modules for easier access
from . import models
from . import sample_data

# Expose commonly used classes and functions
from .models import *
from .sample_data import *

__all__ = [
    # Modules
    'models',
    'sample_data', 
    # 'examples',
    # Re-exported from modules (will be populated by the * imports)
] 