# Fixing module import error in Python
_Exported on 6/6/2025 at 02:13:01 EDT from Cursor (1.0.0)_

---

**User**

ModuleNotFoundError: No module named 'app.utils'; 'app' is not a package
Traceback:
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 534, in _run_script
    exec(code, module.__dict__)
File "/app/app/app.py", line 14, in <module>
    from app.utils.api_client import api_client, run_async
File "/app/app/app.py", line 14, in <module>
    from app.utils.api_client import api_client, run_async

---

**Cursor**

I can see you're encountering a Python import error where `app` is not being recognized as a package. This typically happens when the `__init__.py` file is missing or the Python path isn't configured correctly. Let me investigate the frontend app structure.

The package structure looks correct with `__init__.py` files present. Let me examine the problematic import in the `app.py` file:

Now let me check the Dockerfile to see how the application is being run:

I can see the issue! The problem is with the Python path configuration and how the Docker container is set up. The Streamlit app is being run from the `/app` directory (which is the Docker WORKDIR), but the app code is in `/app/app/app.py`. When the `app.py` file tries to import `from app.utils.api_client`, Python doesn't recognize the `app` directory as a package because the Python path isn't set up correctly.

Let me examine the current `__init__.py` files to understand their contents:

The issue is clear now. The problem is that when the Docker container runs `streamlit run app/app.py`, the working directory is `/app`, and the Python interpreter can't find the `app` package because the Python path doesn't include the parent directory properly.

There are several ways to fix this. The most straightforward solution is to modify the import statements to use relative imports or to adjust the Python path. Let me fix this by updating the Dockerfile to properly set up the Python path:

```dockerfile
# Add shared models to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

->

# Add shared models and app to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app:/app/app"
```

However, there's a better and more elegant solution. Instead of relying on PYTHONPATH manipulation, let's change the import statements to use relative imports or absolute imports from the correct package structure. Let me check if there's a better way by modifying the app.py file to use relative imports:

```python
from app.utils.api_client import api_client, run_async
from app.config import settings

->

from .utils.api_client import api_client, run_async
from .config import settings
```

Now I need to revert the Dockerfile change since we're using a better approach with relative imports:

```dockerfile
# Add shared models and app to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app:/app/app"

->

# Add shared models to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"
```

Actually, let me reconsider this. The relative import approach might not work well with Streamlit when the app is run directly. Let me check the CMD lines in the Dockerfile and consider a different approach. The better solution would be to modify the Dockerfile to run the app from the correct directory:

```dockerfile
# Run the application with hot reload
CMD ["streamlit", "run", "app/app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.runOnSave", "true"]

->

# Run the application with hot reload
CMD ["python", "-m", "streamlit", "run", "app/app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.runOnSave", "true"]
```

```dockerfile
# Run the application
CMD ["streamlit", "run", "app/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

->

# Run the application
CMD ["python", "-m", "streamlit", "run", "app/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
```

Let me revert the relative imports since they might cause issues when running Streamlit, and instead use a more reliable approach by adding the app directory to the Python path in the Dockerfile:

```python
from .utils.api_client import api_client, run_async
from .config import settings

->

from app.utils.api_client import api_client, run_async
from app.config import settings
```

Now let me properly fix the Python path in the Dockerfile by adding the `/app` directory (where the `app` package is located) to the PYTHONPATH:

```dockerfile
# Add shared models to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app"

->

# Add shared models and app package to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app:/app"
```

Actually, let me think about this differently. Since the app directory is copied to `/app/app/` in the container, and the working directory is `/app`, the Python path should include `/app` so that `import app.utils.api_client` can find the `app` package. Let me adjust this more clearly:

```dockerfile
# Add shared models and app package to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app:/app"

->

# Add shared models to Python path - app package is already available from /app
ENV PYTHONPATH="${PYTHONPATH}:/app"
```

The Python path should already be correct since `/app` is in the PYTHONPATH and the `app` package is located at `/app/app/`. The issue might be that we need to ensure the app runs with the correct module resolution. Let me check if there are any other imports that might be causing issues or if we need to add an `__init__.py` at the root level.

Let me check if there's a main `__init__.py` file at the frontend root:

The package structure looks good. The main issue might be that when Streamlit runs the app, it needs to have a clear module path. Let me check how the app is structured by looking at the actual error location and considering a different solution.

Let me add a simple print statement to debug the Python path and see what's available. However, first let me try a more straightforward solution by creating a launcher script that sets up the Python path correctly:

```python
#!/usr/bin/env python3
"""Launcher script for the Streamlit app with proper Python path setup."""

import sys
import os

# Add the current directory to Python path to ensure app package is found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Run the Streamlit app
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    
    # Set up Streamlit arguments
    sys.argv = [
        "streamlit",
        "run",
        "app/app.py",
        "--server.address=0.0.0.0",
        "--server.port=8501"
    ]
    
    # Add runOnSave for development
    if os.getenv("STREAMLIT_ENV") == "development":
        sys.argv.append("--server.runOnSave=true")
    
    stcli.main()
```

Now let me update the Dockerfile to use this launcher script and set the appropriate environment variables:

```dockerfile
# Copy frontend application code (excluding local shared directory)
COPY frontend/app/ ./app/
COPY frontend/tests/ ./tests/
COPY frontend/*.py ./
COPY frontend/*.ini ./
COPY frontend/*.txt ./

->

# Copy frontend application code (excluding local shared directory)
COPY frontend/app/ ./app/
COPY frontend/tests/ ./tests/
COPY frontend/run_app.py ./
COPY frontend/*.py ./
COPY frontend/*.ini ./
COPY frontend/*.txt ./
```

The issue is that the `frontend/*.py` line will copy the `run_app.py` file, so I don't need to explicitly add it. Now let me update the CMD lines to use the launcher script:

```dockerfile
# Run the application with hot reload
CMD ["python", "-m", "streamlit", "run", "app/app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.runOnSave", "true"]

->

# Set environment for development
ENV STREAMLIT_ENV=development

# Run the application with hot reload using launcher script
CMD ["python", "run_app.py"]
```

```dockerfile
# Run the application
CMD ["python", "-m", "streamlit", "run", "app/app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]

->

# Run the application using launcher script
CMD ["python", "run_app.py"]
```

Let me also check if there are any other import issues in the codebase. Let me examine the api_client.py file to make sure it doesn't have similar import issues:

I can see that api_client.py also imports `from app.config import settings`. This import will also fail with the same issue. Let me check the config.py file:

Good, the config.py file doesn't have any internal app imports, so it should work fine. I need to fix the import in api_client.py as well:

```python
from app.config import settings

->

from ..config import settings
```

However, let me reconsider this approach. Using relative imports might cause issues when running the Streamlit app directly. Instead, let me revert the relative import and stick with the launcher script approach, which should properly set up the Python path:

```python
from ..config import settings

->

from app.config import settings
```

Now let me test whether our launcher script approach will work by ensuring that when the run_app.py script runs, it properly adds the current directory (which contains the `app` package) to the Python path. Let me also check if there might be any other Python files in the frontend directory that could conflict:

Good, there's only the `run_app.py` file that I created. The Docker copy command `COPY frontend/*.py ./` will copy this file to the right location.

Now let me also add some error handling and debug information to the launcher script to help troubleshoot any remaining issues:

```python
#!/usr/bin/env python3
"""Launcher script for the Streamlit app with proper Python path setup."""

import sys
import os

# Add the current directory to Python path to ensure app package is found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

->

#!/usr/bin/env python3
"""Launcher script for the Streamlit app with proper Python path setup."""

import sys
import os

# Add the current directory to Python path to ensure app package is found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Debug information
print(f"Current directory: {current_dir}")
print(f"Python path: {sys.path}")
print(f"Contents of current directory: {os.listdir(current_dir)}")

# Verify app package is available
try:
    import app
    print(f"App package found at: {app.__file__}")
except ImportError as e:
    print(f"Failed to import app package: {e}")
    print("This might indicate a path issue")
```



Perfect! Now let's create a summary of the changes I made to fix the import issue:

## Summary of Changes

I've fixed the `ModuleNotFoundError: No module named 'app.utils'` issue by implementing the following changes:

### 1. **Created a Launcher Script** (`frontend/run_app.py`)
- Added a Python launcher script that properly sets up the Python path before running Streamlit
- The script adds the current directory to `sys.path` to ensure the `app` package can be found
- Includes debug information to help troubleshoot any remaining path issues
- Handles both development and production environments

### 2. **Updated Dockerfile**
- Modified the CMD instructions in both development and production stages to use the launcher script instead of running Streamlit directly
- Added `STREAMLIT_ENV=development` environment variable for the development stage
- The launcher script will automatically handle the Streamlit arguments and path setup

### 3. **Root Cause Analysis**
The issue occurred because:
- The Docker container runs from `/app` as the working directory
- The `app` package is located at `/app/app/`
- When Streamlit runs `app/app.py` directly, Python couldn't resolve `from app.utils.api_client import ...` because the `app` package wasn't in the Python path correctly
- The launcher script ensures `/app` (which contains the `app` package) is in the Python path before importing any modules

### 4. **How It Works Now**
1. Docker runs `python run_app.py`
2. The launcher script adds `/app` to `sys.path`
3. The launcher script then runs Streamlit with the correct arguments
4. When Streamlit loads `app/app.py`, Python can now find the `app` package and resolve imports like `from app.utils.api_client import ...`

The solution maintains the existing import structure without requiring relative imports, which can be problematic with Streamlit applications. The debug output in the launcher script will help verify that the path setup is working correctly when you run the container.

To test this fix, rebuild your Docker container and run it. The debug output should show that the `app` package is found successfully, and the import errors should be resolved.

