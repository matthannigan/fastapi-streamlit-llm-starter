# Core Application Imports

This file re-exports the application's central configuration object and
custom exception base classes, making them easily accessible from a single,
stable import path.

## Example

from .core import settings
from .core import ApplicationError (once moved)
