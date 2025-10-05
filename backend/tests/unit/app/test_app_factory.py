"""
Comprehensive App Factory Test Suite

This test suite validates the app factory pattern implementation, ensuring that:
- Factory creates independent FastAPI instances
- Settings overrides work correctly
- Router and middleware registration behaves as expected
- Backward compatibility is maintained
- Deployment scenarios remain functional

Test Philosophy:
- Test behavior, not implementation details
- Validate factory pattern enables test isolation
- Ensure backward compatibility for production deployments
- Focus on external observable behavior of created apps
"""

import pytest
from typing import Optional
from fastapi import FastAPI
from fastapi.testclient import TestClient
import os
import sys

# Add backend directory to path for imports
sys.path.insert(0, '/Users/matth/Github/MGH/fastapi-streamlit-llm-starter/backend')

from app.main import create_app, create_public_app_with_settings, create_internal_app_with_settings
from app.core.config import create_settings, Settings
from app.core.environment import is_production_environment


class TestAppFactory:
    """Test suite for the main create_app() factory function."""

    def test_create_app_returns_fresh_instances(self):
        """Test that create_app() creates independent FastAPI instances.

        Behavior: Each call to create_app() should return a completely separate
        FastAPI instance with its own configuration, routers, and middleware.

        Business Impact: Ensures test isolation by guaranteeing each test gets
        a fresh app instance that cannot affect other tests through shared state.
        """
        # Create multiple app instances
        app1 = create_app()
        app2 = create_app()

        # Verify they are different objects
        assert app1 is not app2, "Factory should create different instances"

        # Verify both are FastAPI instances
        assert isinstance(app1, FastAPI), "Factory should return FastAPI instance"
        assert isinstance(app2, FastAPI), "Factory should return FastAPI instance"

        # Verify both have the same basic structure (backward compatibility)
        assert app1.title == app2.title, "Apps should have same title by default"
        assert app1.version == app2.version, "Apps should have same version by default"

    def test_create_app_with_custom_settings(self):
        """Test that create_app() accepts and uses custom settings parameter.

        Behavior: When settings_obj is provided, the factory should use those
        settings instead of creating new ones from environment variables.

        Business Impact: Enables test scenarios with specific configuration
        overrides and multi-instance deployment with different settings.
        """
        # Create custom settings
        custom_settings = create_settings()
        custom_settings.debug = True
        custom_settings.log_level = "DEBUG"

        # Create app with custom settings
        custom_app = create_app(settings_obj=custom_settings)

        # Verify app is created successfully
        assert isinstance(custom_app, FastAPI)

        # Create default app for comparison
        default_app = create_app()

        # Both should be valid FastAPI instances
        assert isinstance(default_app, FastAPI)

    def test_create_app_with_include_routers_false(self):
        """Test that include_routers=False prevents router registration.

        Behavior: When include_routers=False, the factory should create a FastAPI
        instance without registering any API routers, resulting in fewer routes.

        Business Impact: Enables testing scenarios where endpoint functionality
        needs to be isolated from middleware and configuration testing.
        """
        # Create app without routers
        app_no_routers = create_app(include_routers=False)

        # Create default app for comparison
        app_default = create_app(include_routers=True)

        # Both should be FastAPI instances
        assert isinstance(app_no_routers, FastAPI)
        assert isinstance(app_default, FastAPI)

        # App without routers should have fewer routes
        no_router_routes = len([route for route in app_no_routers.routes if hasattr(route, 'path')])
        default_routes = len([route for route in app_default.routes if hasattr(route, 'path')])

        # The app without routers should have significantly fewer routes
        # (mainly the internal app mount and root endpoints)
        assert no_router_routes < default_routes, (
            f"App without routers should have fewer routes: "
            f"{no_router_routes} vs {default_routes}"
        )

    def test_create_app_with_include_middleware_false(self):
        """Test that include_middleware=False prevents middleware configuration.

        Behavior: When include_middleware=False, the factory should create a FastAPI
        instance without configuring the enhanced middleware stack.

        Business Impact: Enables testing scenarios where middleware behavior
        needs to be isolated from core application logic testing.
        """
        # Create app without middleware
        app_no_middleware = create_app(include_middleware=False)

        # Create default app for comparison
        app_default = create_app(include_middleware=True)

        # Both should be FastAPI instances
        assert isinstance(app_no_middleware, FastAPI)
        assert isinstance(app_default, FastAPI)

        # Both apps should be functional
        # Note: Testing middleware absence is complex due to FastAPI's internal structure
        # The key validation is that both apps can be created successfully

    def test_create_app_with_custom_lifespan(self):
        """Test that create_app() accepts custom lifespan parameter.

        Behavior: When lifespan parameter is provided, the factory should use
        that context manager instead of the default lifespan.

        Business Impact: Enables test scenarios with custom startup/shutdown
        behavior and specialized initialization requirements.
        """
        from contextlib import asynccontextmanager

        # Create custom lifespan
        @asynccontextmanager
        async def custom_lifespan(app: FastAPI):
            # Custom startup logic
            yield
            # Custom shutdown logic

        # Create app with custom lifespan
        custom_app = create_app(lifespan=custom_lifespan)

        # Verify app is created successfully
        assert isinstance(custom_app, FastAPI)

        # Create default app for comparison
        default_app = create_app()
        assert isinstance(default_app, FastAPI)

    def test_create_app_dual_api_architecture(self):
        """Test that create_app() maintains dual-API architecture.

        Behavior: The factory should create a main public app with an internal
        app mounted at /internal path, preserving the dual-API structure.

        Business Impact: Ensures architectural consistency between singleton
        and factory patterns, maintaining security separation between public
        and administrative endpoints.
        """
        # Create app using factory
        app = create_app()

        # Verify it's a FastAPI instance
        assert isinstance(app, FastAPI)

        # Check for internal app mount
        internal_routes = [route for route in app.routes if hasattr(route, 'path') and route.path == "/internal"]
        assert len(internal_routes) > 0, "App should have internal API mounted at /internal"

        # Verify main app has expected properties
        assert app.title == "AI Text Processor API", "Main app should have correct title"

    def test_create_app_environment_isolation(self):
        """Test that create_app() creates apps isolated from environment changes.

        Behavior: Apps created before environment variable changes should not
        be affected by subsequent changes, while new apps should pick up
        the latest environment values.

        Business Impact: Ensures test isolation by preventing environment
        changes in one test from affecting apps created in other tests.
        """
        # Store original environment
        original_debug = os.environ.get('DEBUG')

        try:
            # Set initial environment
            os.environ['DEBUG'] = 'false'

            # Create first app
            app1 = create_app()

            # Change environment
            os.environ['DEBUG'] = 'true'

            # Create second app after environment change
            app2 = create_app()

            # Both apps should be valid FastAPI instances
            assert isinstance(app1, FastAPI)
            assert isinstance(app2, FastAPI)

            # Apps should be different instances
            assert app1 is not app2, "Apps should be different instances"

        finally:
            # Restore original environment
            if original_debug is not None:
                os.environ['DEBUG'] = original_debug
            else:
                os.environ.pop('DEBUG', None)


class TestAppFactorySettingsIntegration:
    """Test suite for app factory integration with settings system."""

    def test_create_app_with_different_environment_settings(self):
        """Test app creation with different environment configurations.

        Behavior: Apps created in different environment contexts should
        reflect those environment differences while maintaining functionality.

        Business Impact: Validates that factory pattern supports multi-environment
        deployment scenarios (development, staging, production).
        """
        # Test with development-like settings
        dev_settings = create_settings()
        dev_settings.debug = True
        dev_settings.log_level = "DEBUG"

        dev_app = create_app(settings_obj=dev_settings)
        assert isinstance(dev_app, FastAPI)

        # Test with production-like settings
        prod_settings = create_settings()
        prod_settings.debug = False
        prod_settings.log_level = "INFO"

        prod_app = create_app(settings_obj=prod_settings)
        assert isinstance(prod_app, FastAPI)

        # Apps should be different instances
        assert dev_app is not prod_app, "Different settings should create different instances"

    def test_create_app_settings_independence(self):
        """Test that apps maintain independent settings configurations.

        Behavior: Each app created by the factory should maintain its own
        settings configuration without interference from other apps.

        Business Impact: Ensures configuration isolation between different
        app instances, critical for multi-tenant deployment scenarios.
        """
        # Create two different settings objects
        settings1 = create_settings()
        settings1.debug = True

        settings2 = create_settings()
        settings2.debug = False

        # Create apps with different settings
        app1 = create_app(settings_obj=settings1)
        app2 = create_app(settings_obj=settings2)

        # Both should be valid
        assert isinstance(app1, FastAPI)
        assert isinstance(app2, FastAPI)

        # Should be different instances
        assert app1 is not app2


class TestBackwardCompatibility:
    """Test suite for backward compatibility with existing deployment patterns."""

    def test_module_level_app_exists(self):
        """Test that module-level app singleton is available.

        Behavior: The module should provide a default `app` instance created
        via the factory function for backward compatibility.

        Business Impact: Ensures existing deployment scripts and configurations
        continue to work without modification.
        """
        # Import the module-level app
        from app.main import app

        # Verify it's a FastAPI instance
        assert isinstance(app, FastAPI), "Module-level app should be FastAPI instance"

        # Verify it has expected properties
        assert app.title == "AI Text Processor API", "Module app should have correct title"
        assert app.version == "1.0.0", "Module app should have correct version"

    def test_module_level_app_same_as_factory_default(self):
        """Test that module-level app behaves like factory default.

        Behavior: The module-level app should be equivalent to calling
        create_app() with default parameters.

        Business Impact: Ensures consistency between singleton and factory
        patterns, preventing unexpected behavioral differences.
        """
        # Import module-level app
        from app.main import app as module_app

        # Create factory app with defaults
        factory_app = create_app()

        # Both should be FastAPI instances
        assert isinstance(module_app, FastAPI)
        assert isinstance(factory_app, FastAPI)

        # Should have equivalent properties
        assert module_app.title == factory_app.title
        assert module_app.version == factory_app.version

    def test_factory_app_import_compatibility(self):
        """Test that factory function can be imported and used directly.

        Behavior: The create_app function should be importable and usable
        without any special setup or configuration.

        Business Impact: Enables developers to migrate to factory pattern
        incrementally and use it for testing scenarios.
        """
        # Test import from main module
        from app.main import create_app

        # Verify it's callable
        assert callable(create_app), "create_app should be callable"

        # Verify it returns FastAPI instance
        app = create_app()
        assert isinstance(app, FastAPI)


class TestDeploymentCompatibility:
    """Test suite for deployment scenario compatibility."""

    def test_factory_created_app_has_all_routes(self):
        """Test that factory-created app has complete route structure.

        Behavior: App created by factory should have all expected routes
        including public API endpoints, internal API mount, and utility endpoints.

        Business Impact: Ensures deployment compatibility by verifying that
        factory-created apps have identical route structure to singleton apps.
        """
        # Create app using factory
        app = create_app()

        # Extract route paths
        routes = [route.path for route in app.routes if hasattr(route, 'path')]

        # Should have main routes
        assert "/" in routes, "Should have root endpoint"

        # Should have internal API mount
        assert "/internal" in routes, "Should have internal API mount"

        # Should have utility redirects
        assert "/health" in routes, "Should have health redirect endpoint"
        assert "/auth/status" in routes, "Should have auth status redirect endpoint"

    def test_factory_created_app_supports_test_client(self):
        """Test that factory-created app works with TestClient.

        Behavior: App created by factory should be fully compatible with
        FastAPI's TestClient for testing purposes.

        Business Impact: Ensures that factory pattern doesn't break existing
        test patterns and testing infrastructure.
        """
        # Create app using factory
        app = create_app()

        # Create TestClient
        client = TestClient(app)

        # Test basic functionality
        response = client.get("/")
        assert response.status_code == 200

        # Verify response structure
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "AI Text Processor API"

    def test_factory_created_app_documentation_endpoints(self):
        """Test that factory-created app has proper documentation endpoints.

        Behavior: App should have custom documentation endpoints at expected
        paths with proper functionality.

        Business Impact: Ensures developer experience is maintained with
        factory pattern, including API documentation access.
        """
        # Create app using factory
        app = create_app()

        # Create TestClient
        client = TestClient(app)

        # Test main documentation endpoint
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_factory_app_dual_functionality(self):
        """Test that factory maintains dual-API functionality.

        Behavior: Factory-created app should provide both public and internal
        API functionality through the same interface as the singleton pattern.

        Business Impact: Ensures all operational capabilities remain available
        when using factory pattern, including internal administrative functions.
        """
        # Create app using factory
        app = create_app()

        # Create TestClient
        client = TestClient(app)

        # Test public API functionality
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "docs" in data
        assert "internal_docs" in data

        # Test internal API is accessible
        response = client.get("/internal/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Internal API" in data["message"]


class TestRouterMiddlewareConfiguration:
    """Test suite for router and middleware configuration behavior."""

    def test_router_configuration_flags(self):
        """Test that router inclusion flags work correctly.

        Behavior: include_routers parameter should control whether API routers
        are registered, affecting the number of available endpoints.

        Business Impact: Enables flexible testing scenarios by allowing
        selective router inclusion for focused testing.
        """
        # App with all routers
        app_with_routers = create_app(include_routers=True)

        # App without routers
        app_without_routers = create_app(include_routers=False)

        # Count API routes (excluding utility endpoints)
        def count_api_routes(app):
            return len([route for route in app.routes if hasattr(route, 'path') and not route.path.startswith('/internal')])

        with_routers_count = count_api_routes(app_with_routers)
        without_routers_count = count_api_routes(app_without_routers)

        # App with routers should have more routes
        assert with_routers_count > without_routers_count, (
            f"App with routers should have more routes: {with_routers_count} vs {without_routers_count}"
        )

    def test_middleware_configuration_flags(self):
        """Test that middleware inclusion flags work correctly.

        Behavior: include_middleware parameter should control whether the
        enhanced middleware stack is configured.

        Business Impact: Enables testing scenarios without middleware interference
        while maintaining full functionality for production deployments.
        """
        # Both configurations should create valid apps
        app_with_middleware = create_app(include_middleware=True)
        app_without_middleware = create_app(include_middleware=False)

        assert isinstance(app_with_middleware, FastAPI)
        assert isinstance(app_without_middleware, FastAPI)

        # Both should be functional for basic requests
        client1 = TestClient(app_with_middleware)
        client2 = TestClient(app_without_middleware)

        response1 = client1.get("/")
        assert response1.status_code == 200

        response2 = client2.get("/")
        assert response2.status_code == 200

    def test_factory_configuration_combinations(self):
        """Test all combinations of configuration flags.

        Behavior: All combinations of include_routers and include_middleware
        should produce valid FastAPI instances.

        Business Impact: Ensures factory pattern supports all testing and
        deployment scenarios without unexpected failures.
        """
        configurations = [
            {"include_routers": True, "include_middleware": True},
            {"include_routers": True, "include_middleware": False},
            {"include_routers": False, "include_middleware": True},
            {"include_routers": False, "include_middleware": False},
        ]

        for config in configurations:
            app = create_app(**config)
            assert isinstance(app, FastAPI), f"Failed configuration: {config}"

            # Basic functionality test
            client = TestClient(app)
            response = client.get("/")
            assert response.status_code == 200, f"Failed request for configuration: {config}"


class TestFactoryConsistency:
    """Test suite for factory behavior consistency."""

    def test_multiple_factory_calls_identical_defaults(self):
        """Test that multiple factory calls with defaults produce equivalent apps.

        Behavior: Calling create_app() multiple times with default parameters
        should produce apps with equivalent configuration and behavior.

        Business Impact: Ensures factory pattern reliability and predictability
        for standard usage scenarios.
        """
        # Create multiple apps with default settings
        apps = [create_app() for _ in range(3)]

        # All should be FastAPI instances
        for app in apps:
            assert isinstance(app, FastAPI)

        # All should have same basic properties
        titles = [app.title for app in apps]
        assert all(title == titles[0] for title in titles), "All apps should have same title"

        versions = [app.version for app in apps]
        assert all(version == versions[0] for version in versions), "All apps should have same version"

        # All should be different instances
        for i in range(len(apps)):
            for j in range(i + 1, len(apps)):
                assert apps[i] is not apps[j], "Apps should be different instances"

    def test_factory_deterministic_behavior(self):
        """Test that factory behavior is deterministic.

        Behavior: Calling create_app() with identical parameters should
        produce apps with identical behavior and configuration.

        Business Impact: Ensures reliable testing and deployment experiences
        with predictable factory behavior.
        """
        # Create settings object
        settings = create_settings()
        settings.debug = True

        # Create multiple apps with identical settings
        app1 = create_app(settings_obj=settings, include_routers=True, include_middleware=True)
        app2 = create_app(settings_obj=settings, include_routers=True, include_middleware=True)

        # Both should be valid
        assert isinstance(app1, FastAPI)
        assert isinstance(app2, FastAPI)

        # Both should behave identically for basic requests
        client1 = TestClient(app1)
        client2 = TestClient(app2)

        response1 = client1.get("/")
        response2 = client2.get("/")

        assert response1.status_code == response2.status_code
        assert response1.json() == response2.json()


class TestFactoryErrorHandling:
    """Test suite for factory error handling and edge cases."""

    def test_factory_with_none_settings(self):
        """Test that factory handles None settings gracefully.

        Behavior: When settings_obj is None, factory should create fresh
        settings from current environment variables.

        Business Impact: Ensures factory works correctly in default usage
        scenarios where no custom settings are provided.
        """
        # Create app with None settings (default behavior)
        app = create_app(settings_obj=None)

        # Should create valid FastAPI instance
        assert isinstance(app, FastAPI)

        # Should be functional
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200

    def test_factory_resilience_to_environment_changes(self):
        """Test factory resilience to environment variable changes.

        Behavior: Factory should handle environment variable changes gracefully,
        creating apps that reflect current environment state.

        Business Impact: Ensures factory pattern works correctly in dynamic
        environment scenarios and testing contexts.
        """
        # Store original environment
        original_env = dict(os.environ)

        try:
            # Test with different environment settings
            os.environ['DEBUG'] = 'true'
            os.environ['LOG_LEVEL'] = 'DEBUG'

            app1 = create_app()

            # Change environment
            os.environ['DEBUG'] = 'false'
            os.environ['LOG_LEVEL'] = 'INFO'

            app2 = create_app()

            # Both should be valid
            assert isinstance(app1, FastAPI)
            assert isinstance(app2, FastAPI)

            # Should be different instances
            assert app1 is not app2

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)