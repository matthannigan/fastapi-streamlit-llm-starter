# Schemas (Data Contracts)

Re-exports all Pydantic models from their original location in the 'shared'
module. This provides a single, consistent import path for all data contracts
used within the FastAPI application.

Once the models are moved to feature-based files within this `schemas`
directory, the imports will be updated to point to those local files.
