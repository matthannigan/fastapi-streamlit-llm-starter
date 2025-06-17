"""
Schemas (Data Contracts)

Re-exports all Pydantic models from their original location in the 'shared'
module. This provides a single, consistent import path for all data contracts
used within the FastAPI application.

Once the models are moved to feature-based files within this `schemas`
directory, the imports will be updated to point to those local files.
"""

# This acts as a bridge to the original 'shared' models during transition.
# Your import_update_script.py should change all imports to point here, e.g.,
# from app.schemas import TextProcessingRequest
from ....shared.shared.models import (
    ProcessingOperation,
    ProcessingStatus,
    TextProcessingRequest,
    TextProcessingResponse,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse,
    BatchProcessingItem,
    SentimentResult,
    ErrorResponse,
    HealthResponse,
    ModelConfiguration,
    UsageStatistics,
    APIKeyValidation,
    ConfigurationUpdate,
    ModelInfo
)

__all__ = [
    "ProcessingOperation",
    "ProcessingStatus",
    "TextProcessingRequest",
    "TextProcessingResponse",
    "BatchTextProcessingRequest",
    "BatchTextProcessingResponse",
    "BatchProcessingItem",
    "SentimentResult",
    "ErrorResponse",
    "HealthResponse",
    "ModelConfiguration",
    "UsageStatistics",
    "APIKeyValidation",
    "ConfigurationUpdate",
    "ModelInfo",
]