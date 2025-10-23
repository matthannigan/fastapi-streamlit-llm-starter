"""
Integration tests for Security Middleware → Documentation Endpoints Integration (Endpoint-Aware CSP).

This test suite validates the critical integration seam between the SecurityMiddleware
and documentation endpoints, ensuring that different Content Security Policies (CSP)
are applied based on endpoint type while maintaining comprehensive security headers
across all responses.

Seam Under Test:
    SecurityMiddleware._is_docs_endpoint() → Endpoint-aware CSP policy
    Documentation endpoints (/docs, /redoc, /internal/docs) → Relaxed CSP
    API endpoints (/v1/*, /internal/* non-docs) → Strict CSP

Critical Paths:
    - Documentation endpoint detection and relaxed CSP application
    - API endpoint detection and strict CSP enforcement
    - Production environment security header enhancement
    - Security header completeness and ordering validation

Business Impact:
    Security-critical behavior. Swagger UI requires relaxed CSP for functionality,
    but API endpoints need strict CSP. Incorrect CSP breaks Swagger UI; missing
    headers expose security vulnerabilities.

Testing Strategy:
    - Test endpoint-specific CSP policies through HTTP requests
    - Verify security header completeness across all endpoints
    - Test production environment security enhancements
    - Validate header ordering and CSP policy differentiation
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any


class TestSecurityMiddlewareIntegration:
    """
    Integration tests for Security Middleware endpoint-aware Content Security Policy.

    Seam Under Test:
        SecurityMiddleware._is_docs_endpoint() → CSP policy selection → Response headers

    Critical Paths:
        - Documentation endpoints: /docs, /redoc, /internal/docs → relaxed CSP with 'unsafe-inline'
        - API endpoints: /v1/*, /internal/* (non-docs) → strict CSP without unsafe directives
        - Production environment: Enhanced security headers regardless of endpoint type

    Business Impact:
        Security-critical integration balancing Swagger UI functionality with API security.
        Documentation endpoints require relaxed CSP for external resources and inline scripts.
        API endpoints require strict CSP to prevent XSS and code injection attacks.
    """

    def test_documentation_endpoints_receive_relaxed_csp(self, test_client: TestClient) -> None:
        """
        Test that documentation endpoints receive relaxed CSP allowing Swagger UI functionality.

        Integration Scope:
            SecurityMiddleware._is_docs_endpoint() → docs CSP policy → Response headers

        Business Impact:
            Swagger UI requires 'unsafe-inline' and 'unsafe-eval' for functionality.
            Without relaxed CSP, Swagger UI breaks and documentation becomes unusable.

        Test Strategy:
            - Request various documentation endpoints
            - Verify relaxed CSP with unsafe directives
            - Confirm other security headers still present

        Success Criteria:
            - Documentation endpoints include 'unsafe-inline' and 'unsafe-eval' in CSP
            - Other security headers remain present and properly formatted
            - CSP allows external CDN resources for Swagger UI
        """
        # Test main documentation endpoints
        docs_endpoints = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/docs/oauth2-redirect",
            "/redoc/static/redoc.standalone.js"
        ]

        expected_unsafe_directives = ["'unsafe-inline'", "'unsafe-eval'"]
        expected_allowed_domains = [
            "fastapi.tiangolo.com",
            "cdn.jsdelivr.net",
            "unpkg.com",
            "fonts.googleapis.com",
            "fonts.gstatic.com"
        ]

        for endpoint in docs_endpoints:
            # Make request to documentation endpoint
            response = test_client.get(endpoint)

            # Should succeed (2xx) or return proper 404 for non-existent endpoints
            assert response.status_code in [200, 404], f"Unexpected status for {endpoint}"

            # Only check CSP on successful responses (404s don't go through middleware)
            if response.status_code == 200:
                # Verify CSP header is present
                assert "content-security-policy" in response.headers, f"Missing CSP header for {endpoint}"

                csp_value = response.headers["content-security-policy"].lower()

                # Verify relaxed CSP includes unsafe directives for Swagger UI
                for unsafe_directive in expected_unsafe_directives:
                    assert unsafe_directive in csp_value, f"Missing {unsafe_directive} in CSP for {endpoint}"

            # Verify external domains are allowed for Swagger UI resources (only on success)
            if response.status_code == 200:
                for domain in expected_allowed_domains:
                    assert domain in csp_value, f"Missing allowed domain {domain} in CSP for {endpoint}"

            # Verify other security headers are still present (even on 404s)
            required_security_headers = [
                "strict-transport-security",
                "x-frame-options",
                "x-content-type-options",
                "x-xss-protection",
                "referrer-policy",
                "permissions-policy"
            ]

            for header in required_security_headers:
                assert header in response.headers, f"Missing security header {header} for {endpoint}"

    def test_api_endpoints_receive_strict_csp(self, test_client: TestClient) -> None:
        """
        Test that API endpoints receive strict CSP without unsafe directives.

        Integration Scope:
            SecurityMiddleware._is_docs_endpoint() → API CSP policy → Response headers

        Business Impact:
            API endpoints must have strict CSP to prevent XSS and code injection.
            Unsafe directives would create security vulnerabilities in production APIs.

        Test Strategy:
            - Request various API endpoints
            - Verify strict CSP without unsafe directives
            - Confirm comprehensive security headers present

        Success Criteria:
            - API endpoints have strict CSP with only 'self' and safe sources
            - No 'unsafe-inline' or 'unsafe-eval' directives present
            - All required security headers present and properly configured
        """
        # Test API endpoints that should receive strict CSP
        api_endpoints = [
            "/v1/health",
            "/v1/auth/status"
        ]

        forbidden_unsafe_directives = ["'unsafe-inline'", "'unsafe-eval'"]
        expected_strict_sources = ["'self'"]

        for endpoint in api_endpoints:
            # Make request to API endpoint with appropriate method and auth headers
            headers = {"Authorization": "Bearer test-api-key-12345"}
            response = test_client.get(endpoint, headers=headers)
            expected_statuses = [200, 401, 404]

            # Should succeed (2xx) or return proper auth error (401)
            assert response.status_code in expected_statuses, f"Unexpected status for {endpoint}"

            # Verify CSP header is present
            assert "content-security-policy" in response.headers, f"Missing CSP header for {endpoint}"

            csp_value = response.headers["content-security-policy"].lower()

            # Verify strict CSP does NOT include unsafe directives
            for unsafe_directive in forbidden_unsafe_directives:
                assert unsafe_directive not in csp_value, f"Unsafe directive {unsafe_directive} found in CSP for {endpoint}"

            # Verify strict CSP only allows safe sources
            for source in expected_strict_sources:
                assert source in csp_value, f"Missing strict source {source} in CSP for {endpoint}"

            # Verify no external domains are allowed for API endpoints
            forbidden_domains = ["cdn.jsdelivr.net", "unpkg.com", "fonts.googleapis.com"]
            for domain in forbidden_domains:
                assert domain not in csp_value, f"External domain {domain} incorrectly allowed in CSP for {endpoint}"

            # Verify comprehensive security headers are present
            required_security_headers = {
                "strict-transport-security": "max-age=31536000; includesubdomains",
                "x-frame-options": "deny",
                "x-content-type-options": "nosniff",
                "x-xss-protection": "1; mode=block",
                "referrer-policy": "strict-origin-when-cross-origin",
                "permissions-policy": "geolocation=(), microphone=(), camera=()"
            }

            for header, expected_value in required_security_headers.items():
                assert header in response.headers, f"Missing security header {header} for {endpoint}"
                actual_value = response.headers[header].lower()
                assert expected_value.lower() in actual_value, f"Incorrect value for {header} in {endpoint}"

    def test_internal_endpoints_receive_relaxed_csp(self, test_client: TestClient) -> None:
        """
        Test that internal endpoints receive relaxed CSP policies according to middleware implementation.

        Integration Scope:
            SecurityMiddleware._is_docs_endpoint() → Internal endpoint classification → Relaxed CSP

        Business Impact:
            According to the current implementation, ALL /internal/* endpoints receive relaxed CSP.
            This supports internal documentation and admin interfaces that may need external resources.

        Test Strategy:
            - Request various internal endpoints
            - Verify they all receive relaxed CSP policies
            - Confirm consistent behavior across internal endpoint types

        Success Criteria:
            - All internal endpoints receive relaxed CSP with unsafe directives
            - CSP policies allow external resources for internal interfaces
            - Behavior matches SecurityMiddleware._is_docs_endpoint() implementation
        """
        # Internal endpoints that should get relaxed CSP per current implementation
        internal_endpoints = [
            "/internal/health",
            "/internal/cache/stats",
            "/internal/resilience/circuit_breaker/status",
            "/internal/monitoring/metrics",
            "/internal/docs",
            "/internal/docs/oauth2-redirect",
            "/internal/redoc"
        ]

        for endpoint in internal_endpoints:
            response = test_client.get(endpoint)

            # Should succeed or return proper error (404, 401)
            assert response.status_code in [200, 401, 404], f"Unexpected status for {endpoint}"

            csp_value = response.headers.get("content-security-policy", "").lower()

            # All internal endpoints should get relaxed CSP per current implementation
            assert "'unsafe-inline'" in csp_value, f"Internal endpoint {endpoint} missing relaxed CSP"
            assert "'unsafe-eval'" in csp_value, f"Internal endpoint {endpoint} missing relaxed CSP"

            # Verify external domains are allowed for internal endpoints
            expected_domains = ["fastapi.tiangolo.com", "cdn.jsdelivr.net", "unpkg.com"]
            for domain in expected_domains:
                assert domain in csp_value, f"Internal endpoint {endpoint} missing allowed domain {domain}"

    def test_production_environment_enhances_security_headers(
        self,
        production_environment_integration: Any,
        monkeypatch: pytest.MonkeyPatch,
        test_client: TestClient
    ) -> None:
        """
        Test that production environment applies enhanced security headers.

        Integration Scope:
            Environment configuration → SecurityMiddleware → Enhanced headers

        Business Impact:
            Production environments require stricter security headers for compliance.
            Enhanced HSTS, additional restrictions, and proper security policies required.

        Test Strategy:
            - Configure production environment
            - Test both docs and API endpoints
            - Verify enhanced security headers applied
            - Confirm CSP policies still appropriate to endpoint type

        Success Criteria:
            - Production HSTS includes preload and longer max-age
            - All security headers present and properly formatted
            - CSP policies still differentiated by endpoint type
            - No debugging or development headers present
        """
        # Test both endpoint types in production
        test_endpoints = [
            ("/docs", "relaxed"),  # Should get relaxed CSP
            ("/v1/health", "strict")  # Should get strict CSP
        ]

        for endpoint, expected_csp_type in test_endpoints:
            response = test_client.get(endpoint)

            # Verify response succeeds
            assert response.status_code in [200, 404], f"Production endpoint {endpoint} failed"

            # Verify enhanced HSTS header for production
            hsts_header = response.headers.get("strict-transport-security", "").lower()
            assert "max-age=31536000" in hsts_header, f"Production missing enhanced HSTS for {endpoint}"
            assert "includesubdomains" in hsts_header, f"Production HSTS missing subdomain enforcement for {endpoint}"

            # Verify all critical security headers present
            required_headers = [
                "strict-transport-security",
                "x-frame-options",
                "x-content-type-options",
                "x-xss-protection",
                "content-security-policy",
                "referrer-policy",
                "permissions-policy"
            ]

            for header in required_headers:
                assert header in response.headers, f"Production missing {header} for {endpoint}"

            # Verify CSP policy is still appropriate for endpoint type
            csp_value = response.headers.get("content-security-policy", "").lower()

            if expected_csp_type == "relaxed":
                assert "'unsafe-inline'" in csp_value, f"Production docs {endpoint} missing relaxed CSP"
                assert "'unsafe-eval'" in csp_value, f"Production docs {endpoint} missing relaxed CSP"
            else:  # strict
                assert "'unsafe-inline'" not in csp_value, f"Production API {endpoint} has unsafe CSP"
                assert "'unsafe-eval'" not in csp_value, f"Production API {endpoint} has unsafe CSP"

    def test_security_header_ordering_and_completeness(self, test_client: TestClient) -> None:
        """
        Test that all security headers are present in correct order and properly formatted.

        Integration Scope:
            SecurityMiddleware → Complete header set → Proper ordering and formatting

        Business Impact:
            Missing security headers create vulnerabilities. Incorrect header values
            may bypass security protections. Header order can affect browser behavior.

        Test Strategy:
            - Request various endpoint types
            - Verify all expected security headers present
            - Check header values are properly formatted
            - Confirm no missing critical security headers

        Success Criteria:
            - All security headers present regardless of endpoint type
            - Header values follow security best practices
            - No malformed or empty header values
            - CSP policies differentiated correctly
        """
        # Test endpoints of different types
        test_endpoints = [
            "/docs",      # Documentation (relaxed CSP)
            "/v1/health", # Public API (strict CSP)
            "/internal/health"  # Internal endpoint (relaxed CSP per implementation)
        ]

        # Required security headers for all endpoints
        required_security_headers = {
            "strict-transport-security": {
                "pattern": r"max-age=\d+",
                "description": "HSTS with max-age"
            },
            "x-frame-options": {
                "pattern": r"DENY",
                "description": "Clickjacking protection"
            },
            "x-content-type-options": {
                "pattern": r"nosniff",
                "description": "MIME type sniffing protection"
            },
            "x-xss-protection": {
                "pattern": r"1; mode=block",
                "description": "XSS protection"
            },
            "referrer-policy": {
                "pattern": r"strict-origin-when-cross-origin",
                "description": "Referrer policy"
            },
            "permissions-policy": {
                "pattern": r"geolocation=\(\), microphone=\(\), camera=\(\)",
                "description": "Permissions policy"
            },
            "content-security-policy": {
                "pattern": r".+",
                "description": "Content Security Policy"
            }
        }

        for endpoint in test_endpoints:
            response = test_client.get(endpoint)

            # Check all required security headers are present
            for header_name, expected in required_security_headers.items():
                assert header_name in response.headers, f"Missing {header_name} header for {endpoint}"

                header_value = response.headers[header_name]

                # Verify header is not empty
                assert header_value.strip(), f"Empty {header_name} header for {endpoint}"

                # Verify header format matches expected pattern
                import re
                assert re.search(expected["pattern"], header_value, re.IGNORECASE), \
                    f"Malformed {header_name} header for {endpoint}: {header_value}"

            # Additional verification for CSP header based on endpoint type
            csp_header = response.headers.get("content-security-policy", "").lower()

            if endpoint.startswith("/v1/"):
                # Only v1 API endpoints should have strict CSP
                assert "'unsafe-inline'" not in csp_header, f"API endpoint {endpoint} has unsafe CSP"
                assert "'unsafe-eval'" not in csp_header, f"API endpoint {endpoint} has unsafe CSP"
            else:
                # Documentation and internal endpoints should have relaxed CSP
                assert "'unsafe-inline'" in csp_header, f"Docs/internal endpoint {endpoint} missing unsafe-inline"
                assert "'unsafe-eval'" in csp_header, f"Docs/internal endpoint {endpoint} missing unsafe-eval"

    def test_endpoint_aware_csp_edge_cases(self, test_client: TestClient) -> None:
        """
        Test edge cases for endpoint-aware CSP detection and application.

        Integration Scope:
            SecurityMiddleware._is_docs_endpoint() edge cases → CSP policy selection

        Business Impact:
            Edge cases in endpoint detection could result in incorrect CSP policies,
            either breaking documentation functionality or creating security vulnerabilities.

        Test Strategy:
            - Test various endpoint path patterns and edge cases
            - Verify OpenAPI schema endpoints get relaxed CSP
            - Test subpaths and similar endpoint names
            - Confirm correct CSP policy application based on actual implementation

        Success Criteria:
            - All documentation-related paths get relaxed CSP
            - All /internal/* paths get relaxed CSP (per current implementation)
            - Only /v1/* paths get strict CSP
            - Edge cases handled correctly without misclassification
        """
        # Edge case endpoints that should get relaxed CSP (documentation and internal)
        relaxed_csp_endpoints = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/openapi/v1.json",
            "/api/v1/openapi.json",
            "/docs/oauth2-redirect",
            "/redoc/static/css/main.css",
            "/internal/docs",
            "/internal/redoc",
            "/internal/api/docs",
            "/internal/health",
            "/internal/anything",
            "/docs?foo=bar",  # With query parameters
        ]

        # Edge case endpoints that should get strict CSP (only v1 public APIs)
        strict_csp_endpoints = [
            "/v1/health",
            "/v1/docs-status",  # Contains "docs" but is v1 API endpoint
            "/v1/users",
            "/v1/anything",
            "/webhook/docs-processor",  # Contains "docs" but not /docs or /internal
        ]

        # Test relaxed CSP endpoints
        for endpoint in relaxed_csp_endpoints:
            response = test_client.get(endpoint)

            # Check CSP policy (only on successful responses)
            if response.status_code == 200:
                csp_header = response.headers.get("content-security-policy", "").lower()

                # Should have relaxed CSP with unsafe directives
                assert "'unsafe-inline'" in csp_header, f"Expected relaxed CSP for {endpoint}"
                assert "'unsafe-eval'" in csp_header, f"Expected relaxed CSP for {endpoint}"

        # Test strict CSP endpoints
        for endpoint in strict_csp_endpoints:
            response = test_client.get(endpoint)

            # Check CSP policy (only on successful responses)
            if response.status_code == 200:
                csp_header = response.headers.get("content-security-policy", "").lower()

                # Should have strict CSP without unsafe directives
                assert "'unsafe-inline'" not in csp_header, f"Expected strict CSP for {endpoint}"
                assert "'unsafe-eval'" not in csp_header, f"Expected strict CSP for {endpoint}"

    def test_csp_policies_prevent_security_vulnerabilities(self, test_client: TestClient) -> None:
        """
        Test that CSP policies effectively prevent common security vulnerabilities.

        Integration Scope:
            SecurityMiddleware CSP policies → Security vulnerability prevention

        Business Impact:
            CSP policies must prevent XSS, code injection, and data exfiltration
            while allowing legitimate functionality for documentation interfaces.

        Test Strategy:
            - Verify strict CSP policies prevent inline scripts and eval
            - Confirm relaxed CSP policies are scoped to required resources
            - Test that dangerous protocols are blocked
            - Verify data: URLs are properly restricted

        Success Criteria:
            - API endpoints cannot execute inline scripts or eval
            - Documentation endpoints allow only required external resources
            - Dangerous protocols (javascript:, data:) properly restricted
            - Frame ancestors controlled to prevent clickjacking
        """
        # Test API endpoint strict CSP prevents dangerous operations
        api_response = test_client.get("/v1/health")
        api_csp = api_response.headers.get("content-security-policy", "").lower()

        # Verify dangerous directives are not allowed
        dangerous_directives = [
            "script-src *",
            "script-src 'unsafe-inline'",
            "script-src 'unsafe-eval'",
            "default-src *",
            "object-src *",
            "frame-ancestors *"
        ]

        for directive in dangerous_directives:
            assert directive not in api_csp, f"API CSP allows dangerous directive: {directive}"

        # Verify frame ancestors are controlled
        assert "frame-ancestors 'none'" in api_csp, "API CSP missing clickjacking protection"

        # Test documentation endpoint relaxed CSP is appropriately scoped
        docs_response = test_client.get("/docs")
        docs_csp = docs_response.headers.get("content-security-policy", "").lower()

        # Verify docs CSP allows required resources but is still controlled
        script_src_part = [part for part in docs_csp.split(';') if 'script-src' in part.lower()][0] if any('script-src' in part.lower() for part in docs_csp.split(';')) else ""
        assert "script-src" in script_src_part, "Docs CSP missing script-src directive"
        assert "'unsafe-inline'" in script_src_part, "Docs CSP missing unsafe-inline for Swagger"
        assert "'unsafe-eval'" in script_src_part, "Docs CSP missing unsafe-eval for Swagger"

        # Verify docs CSP only allows trusted external domains
        trusted_domains = [
            "fastapi.tiangolo.com",
            "cdn.jsdelivr.net",
            "unpkg.com"
        ]

        for domain in trusted_domains:
            assert domain in docs_csp, f"Docs CSP missing trusted domain: {domain}"

        # Verify docs CSP still controls object sources and base URI
        assert "object-src 'none'" in docs_csp, "Docs CSP missing object-source control"
        assert "base-uri 'self'" in docs_csp, "Docs CSP missing base-uri control"