#!/usr/bin/env python3
"""
Debug Middleware Stack Detection

This script analyzes how FastAPI organizes middleware internally
to fix the middleware detection issue in our validation.
"""

import os
from fastapi import FastAPI

# Set environment for testing
os.environ['RATE_LIMITING_ENABLED'] = 'true'
os.environ['COMPRESSION_ENABLED'] = 'true'
os.environ['SECURITY_HEADERS_ENABLED'] = 'true'
os.environ['API_VERSIONING_ENABLED'] = 'true'
os.environ['PYTHONPATH'] = '/Users/matth/Github/MGH/fastapi-streamlit-llm-starter/backend'

from app.core.config import Settings
from app.core.middleware import setup_enhanced_middleware

def debug_middleware_stack():
    """Debug middleware stack to understand FastAPI's internal structure."""
    print("=== FastAPI Middleware Stack Analysis ===\n")
    
    # Create FastAPI app and settings
    app = FastAPI()
    settings = Settings()
    
    print("1. Initial app state:")
    print(f"   app.__dict__.keys(): {list(app.__dict__.keys())}")
    print(f"   hasattr(app, 'middleware_stack'): {hasattr(app, 'middleware_stack')}")
    print(f"   getattr(app, 'middleware_stack', None): {getattr(app, 'middleware_stack', None)}")
    print()
    
    # Set up middleware
    print("2. Setting up middleware...")
    setup_enhanced_middleware(app, settings)
    print("   Middleware setup complete")
    print()
    
    print("3. After middleware setup:")
    print(f"   hasattr(app, 'middleware_stack'): {hasattr(app, 'middleware_stack')}")
    print(f"   app.middleware_stack: {getattr(app, 'middleware_stack', None)}")
    print()
    
    # Check all attributes that might contain middleware info
    print("4. All app attributes containing 'middleware':")
    for attr in dir(app):
        if 'middleware' in attr.lower():
            value = getattr(app, attr, None)
            print(f"   {attr}: {type(value)} = {value}")
    print()
    
    # Check user_middleware specifically
    print("5. Checking user_middleware:")
    user_middleware = getattr(app, 'user_middleware', None)
    if user_middleware:
        print(f"   Length: {len(user_middleware)}")
        for i, mw in enumerate(user_middleware):
            print(f"   [{i}] {type(mw)} - {mw}")
            if hasattr(mw, 'cls'):
                print(f"       cls: {mw.cls}")
                print(f"       args: {mw.args}")
                print(f"       kwargs: {mw.kwargs}")
    else:
        print("   user_middleware is None")
    print()
    
    # Check router info
    print("6. Router middleware info:")
    if hasattr(app, 'router'):
        router = app.router
        print(f"   router type: {type(router)}")
        for attr in dir(router):
            if 'middleware' in attr.lower():
                value = getattr(router, attr, None)
                print(f"   router.{attr}: {type(value)} = {value}")
    print()
    
    # Try building the application to see if middleware_stack gets populated
    print("7. Building application...")
    try:
        # This might populate middleware_stack
        app.build_middleware_stack()
        print("   Application built successfully")
        print(f"   middleware_stack after build: {getattr(app, 'middleware_stack', None)}")
        if hasattr(app, 'middleware_stack') and app.middleware_stack:
            print(f"   Stack length: {len(app.middleware_stack)}")
    except Exception as e:
        print(f"   Build failed: {e}")
    print()

if __name__ == "__main__":
    debug_middleware_stack()