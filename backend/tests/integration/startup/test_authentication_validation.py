"""
Integration tests for Redis authentication validation (SEAM 5).

This test module verifies the integration between Redis authentication validation,
URL parsing, password strength checking, and environment-aware authentication
requirements.

Test Coverage:
    - URL-embedded credential detection and parsing
    - Weak password warning generation
    - Production authentication enforcement
    - Environment-aware authentication requirements
    - Authentication method detection (URL vs separate password)

Integration Seam:
    validate_redis_auth() → URL parsing → Password strength check → Environment detection → Result generation
"""



class TestRedisAuthenticationValidation:
    """
    Test suite for Redis authentication validation integration.

    Integration Scope:
        Tests the integration of validate_redis_auth() with:
        - URL credential parsing logic
        - Password strength validation
        - Environment detection for auth requirements
        - Authentication method detection
        - Warning and error generation

    Critical Path:
        Redis URL → Authentication detection → Password strength check →
        Environment-aware validation → Result dictionary

    Business Impact:
        Ensures Redis authentication is properly configured for production,
        preventing unauthorized access and enforcing security standards.

    Test Strategy:
        - Test outside-in from validate_redis_auth() entry point
        - Use real URL parsing (no mocking of internal parsing)
        - Verify observable behavior through result dictionary
        - Test environment-aware requirements with monkeypatch
        - Use realistic Redis URL formats
    """

    def test_url_embedded_credentials_detected(self):
        """
        Test that authentication credentials embedded in Redis URL are correctly detected.

        Integration Scope:
            Redis URL → Authentication parsing → Validation success

        Business Impact:
            Ensures Redis authentication is recognized when configured via URL,
            allowing authenticated connections to proceed without false negatives.

        Test Strategy:
            1. Create Redis URL with embedded credentials (user:pass@host)
            2. Call validate_redis_auth() with authenticated URL
            3. Verify authentication is detected and validated
            4. Verify username is correctly extracted

        Success Criteria:
            - result["valid"] is True
            - result["auth_info"]["method"] is "URL-embedded credentials"
            - result["auth_info"]["username"] contains parsed username
            - result["auth_info"]["status"] is "Present"
        """
        # Arrange: Create Redis URL with strong embedded credentials
        from app.core.startup.redis_security import RedisSecurityValidator

        redis_url = "redis://user:strongpassword123456@redis:6379"

        # Act: Validate authentication in URL
        validator = RedisSecurityValidator()
        result = validator.validate_redis_auth(redis_url)

        # Assert: Verify authentication is detected
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "valid" in result, "Result must have 'valid' key"
        assert result["valid"] is True, "Validation should pass for authenticated URL"

        # Verify authentication method is detected
        assert "auth_info" in result, "Result must have 'auth_info' key"
        auth_info = result["auth_info"]
        assert auth_info["method"] == "URL-embedded credentials", \
            "Authentication method should be URL-embedded"
        assert auth_info["status"] == "Present", \
            "Authentication status should be Present"

        # Verify username is extracted
        assert "username" in auth_info, "auth_info should contain username"
        assert auth_info["username"] == "user", \
            "Username should be correctly parsed from URL"

    def test_weak_password_generates_warning(self):
        """
        Test that weak passwords generate security warnings while still passing validation.

        Integration Scope:
            Redis URL → Password strength check → Warning generation

        Business Impact:
            Encourages strong authentication credentials while not blocking
            deployments, supporting security awareness and gradual hardening.

        Test Strategy:
            1. Create Redis URL with weak password (< 16 characters)
            2. Call validate_redis_auth()
            3. Verify validation passes (authentication is present)
            4. Verify warning is generated about password strength

        Success Criteria:
            - result["valid"] is True (auth is configured)
            - result["warnings"] contains weak password warning
            - Warning mentions password length requirement (16+ characters)
            - Warning is clear and actionable
        """
        # Arrange: Create Redis URL with weak password
        from app.core.startup.redis_security import RedisSecurityValidator

        redis_url = "redis://user:weak@redis:6379"  # Password is only 4 characters

        # Act: Validate authentication with weak password
        validator = RedisSecurityValidator()
        result = validator.validate_redis_auth(redis_url)

        # Assert: Verify validation passes but warning is generated
        assert result["valid"] is True, \
            "Validation should pass when authentication is present, even if weak"

        # Verify weak password warning is generated
        assert "warnings" in result, "Result must have 'warnings' key"
        assert isinstance(result["warnings"], list), "Warnings must be a list"
        assert len(result["warnings"]) > 0, \
            "Warning should be generated for weak password"

        # Verify warning content
        warning_message = result["warnings"][0]
        assert "weak password" in warning_message.lower(), \
            "Warning should mention weak password"
        assert "16+ characters" in warning_message, \
            "Warning should recommend 16+ character passwords"

        # Verify authentication is still recognized
        auth_info = result["auth_info"]
        assert auth_info["status"] == "Present", \
            "Authentication should be recognized despite weak password"

    def test_production_requires_authentication(self, monkeypatch):
        """
        Test that production environment requires authentication configuration.

        Integration Scope:
            Environment detection → Auth validation → Production enforcement

        Business Impact:
            Enforces authentication requirement in production, preventing
            unauthorized Redis access and maintaining security compliance.

        Test Strategy:
            1. Configure production environment via monkeypatch.setenv()
            2. Create Redis URL without authentication
            3. Call validate_redis_auth()
            4. Verify validation fails with clear error message

        Success Criteria:
            - result["valid"] is False
            - result["errors"] contains "no authentication configured" message
            - Error mentions production environment requirement
            - Authentication status is "Missing"
        """
        # Arrange: Configure production environment and unauthenticated URL
        from app.core.startup.redis_security import RedisSecurityValidator

        # Set production environment using monkeypatch
        monkeypatch.setenv("ENVIRONMENT", "production")

        redis_url = "redis://redis:6379"  # No authentication

        # Act: Validate authentication in production without auth
        validator = RedisSecurityValidator()
        result = validator.validate_redis_auth(redis_url)

        # Assert: Verify validation fails in production without authentication
        assert result["valid"] is False, \
            "Validation should fail in production without authentication"

        # Verify error message is clear and actionable
        assert "errors" in result, "Result must have 'errors' key"
        assert isinstance(result["errors"], list), "Errors must be a list"
        assert len(result["errors"]) > 0, \
            "Error should be generated for missing authentication in production"

        # Verify error mentions production and authentication
        error_message = result["errors"][0]
        assert "no authentication configured" in error_message.lower(), \
            "Error should mention missing authentication"
        assert "production" in error_message.lower(), \
            "Error should mention production environment"

        # Verify authentication status
        auth_info = result["auth_info"]
        assert auth_info["status"] == "Missing", \
            "Authentication status should be Missing"


class TestRedisAuthenticationMethodDetection:
    """
    Test suite for Redis authentication method detection integration.

    Integration Scope:
        Tests authentication detection for different configuration methods:
        - URL-embedded credentials
        - Separate password parameter
        - Password-only URL format

    Business Impact:
        Supports varied authentication configuration methods, providing
        flexibility while maintaining security validation.

    Test Strategy:
        - Test each authentication method independently
        - Verify method is correctly identified
        - Test method-specific validation behavior
        - Use realistic Redis URL formats
    """

    def test_separate_password_parameter_detected(self):
        """
        Test that separate password parameter is correctly detected and validated.

        Integration Scope:
            URL without auth + password parameter → Authentication detection → Validation

        Business Impact:
            Supports configuration where Redis password is provided separately
            from URL, enabling secure configuration management practices.

        Test Strategy:
            1. Create Redis URL without embedded authentication
            2. Provide password via auth_password parameter
            3. Call validate_redis_auth()
            4. Verify authentication is recognized as separate configuration

        Success Criteria:
            - result["valid"] is True
            - result["auth_info"]["method"] is "Separate password configuration"
            - result["auth_info"]["status"] is "Present"
            - Authentication is validated successfully
        """
        # Arrange: Create URL without auth and separate password
        from app.core.startup.redis_security import RedisSecurityValidator

        redis_url = "redis://redis:6379"  # No auth in URL
        separate_password = "strong_password_123456"  # Strong password

        # Act: Validate authentication with separate password
        validator = RedisSecurityValidator()
        result = validator.validate_redis_auth(
            redis_url=redis_url,
            auth_password=separate_password
        )

        # Assert: Verify separate password is detected
        assert result["valid"] is True, \
            "Validation should pass with separate password"

        # Verify authentication method
        auth_info = result["auth_info"]
        assert auth_info["method"] == "Separate password configuration", \
            "Authentication method should be separate password"
        assert auth_info["status"] == "Present", \
            "Authentication status should be Present"

    def test_password_only_url_format_detected(self):
        """
        Test that password-only URL format (redis://:password@host) is detected.

        Integration Scope:
            Password-only URL → URL parsing → Authentication detection

        Business Impact:
            Supports Redis authentication format where only password is used
            (default username), accommodating common Redis configuration patterns.

        Test Strategy:
            1. Create Redis URL with :password@host format (no username)
            2. Call validate_redis_auth()
            3. Verify authentication is detected
            4. Verify password-only format is recognized

        Success Criteria:
            - result["valid"] is True
            - result["auth_info"]["method"] is "URL-embedded credentials"
            - result["auth_info"]["status"] is "Present"
            - Password-only format is handled correctly
        """
        # Arrange: Create password-only Redis URL
        from app.core.startup.redis_security import RedisSecurityValidator

        redis_url = "redis://:strongpassword123456@redis:6379"  # Password-only format

        # Act: Validate authentication with password-only URL
        validator = RedisSecurityValidator()
        result = validator.validate_redis_auth(redis_url)

        # Assert: Verify password-only authentication is detected
        assert result["valid"] is True, \
            "Validation should pass for password-only URL format"

        # Verify authentication is recognized
        auth_info = result["auth_info"]
        assert auth_info["method"] == "URL-embedded credentials", \
            "Authentication method should be URL-embedded"
        assert auth_info["status"] == "Present", \
            "Authentication status should be Present"


class TestRedisAuthenticationEnvironmentAwareness:
    """
    Test suite for environment-aware authentication validation.

    Integration Scope:
        Tests authentication validation behavior across different environments,
        verifying environment-specific requirements and messaging.

    Business Impact:
        Enables flexible development while enforcing production security,
        supporting efficient local development without compromising production safety.

    Test Strategy:
        - Test authentication requirements in each environment
        - Verify environment-specific error/warning messages
        - Use monkeypatch for environment configuration
        - Test both pass and fail scenarios per environment
    """

    def test_development_allows_missing_authentication_with_warning(self, monkeypatch):
        """
        Test that development environment allows missing authentication with warning.

        Integration Scope:
            Development environment → Auth validation → Warning generation

        Business Impact:
            Enables productive local development without authentication setup
            while maintaining security awareness through warnings.

        Test Strategy:
            1. Configure development environment via monkeypatch.setenv()
            2. Create Redis URL without authentication
            3. Call validate_redis_auth()
            4. Verify validation passes with warning

        Success Criteria:
            - result["valid"] is True (development flexibility)
            - result["warnings"] contains development-specific warning
            - Warning mentions "acceptable for development only"
            - Authentication status is "Missing" but validation passes
        """
        # Arrange: Configure development environment and local Redis URL
        from app.core.startup.redis_security import RedisSecurityValidator

        # Set development environment using monkeypatch
        monkeypatch.setenv("ENVIRONMENT", "development")

        redis_url = "redis://localhost:6379"  # No authentication

        # Act: Validate authentication in development without auth
        validator = RedisSecurityValidator()
        result = validator.validate_redis_auth(redis_url)

        # Assert: Verify validation passes in development
        assert result["valid"] is True, \
            "Validation should pass in development without authentication"

        # Verify warning is generated
        assert "warnings" in result, "Result must have 'warnings' key"
        assert len(result["warnings"]) > 0, \
            "Warning should be generated for missing auth in development"

        # Verify warning mentions development flexibility
        warning_message = result["warnings"][0]
        assert "development only" in warning_message.lower(), \
            "Warning should mention development-only acceptability"
        assert "acceptable" in warning_message.lower(), \
            "Warning should indicate missing auth is acceptable for development"

        # Verify authentication status
        auth_info = result["auth_info"]
        assert auth_info["status"] == "Missing", \
            "Authentication status should be Missing"

    def test_production_rejects_missing_authentication(self, monkeypatch):
        """
        Test that production environment rejects missing authentication.

        Integration Scope:
            Production environment → Auth validation → Error generation

        Business Impact:
            Enforces security standards in production, preventing unauthorized
            Redis access and maintaining compliance requirements.

        Test Strategy:
            1. Configure production environment via monkeypatch.setenv()
            2. Create Redis URL without authentication
            3. Call validate_redis_auth()
            4. Verify validation fails with production-specific error

        Success Criteria:
            - result["valid"] is False
            - result["errors"] contains production-specific error
            - Error mentions "production environment" requirement
            - Error is clear and actionable
        """
        # Arrange: Configure production environment and unauthenticated URL
        from app.core.startup.redis_security import RedisSecurityValidator

        # Set production environment using monkeypatch
        monkeypatch.setenv("ENVIRONMENT", "production")

        redis_url = "redis://redis.production.internal:6379"  # No authentication

        # Act: Validate authentication in production without auth
        validator = RedisSecurityValidator()
        result = validator.validate_redis_auth(redis_url)

        # Assert: Verify validation fails in production
        assert result["valid"] is False, \
            "Validation must fail in production without authentication"

        # Verify production-specific error is generated
        assert "errors" in result, "Result must have 'errors' key"
        assert len(result["errors"]) > 0, \
            "Production should require authentication"

        # Verify error mentions production requirement
        error_message = result["errors"][0]
        assert "production environment" in error_message.lower(), \
            "Error should mention production environment requirement"
        assert "authentication" in error_message.lower(), \
            "Error should mention authentication requirement"

    def test_staging_authentication_requirements(self, monkeypatch):
        """
        Test authentication requirements in staging environment.

        Integration Scope:
            Staging environment → Auth validation → Environment-specific behavior

        Business Impact:
            Ensures staging environment has appropriate security posture,
            balancing production-like requirements with testing flexibility.

        Test Strategy:
            1. Configure staging environment via monkeypatch.setenv()
            2. Test both authenticated and unauthenticated scenarios
            3. Verify staging-specific validation behavior
            4. Verify appropriate warnings or errors

        Success Criteria:
            - Staging behavior is consistent with security policy
            - Validation results are clear and appropriate
            - Environment-specific messaging is present
        """
        # Arrange: Configure staging environment
        from app.core.startup.redis_security import RedisSecurityValidator

        # Set staging environment using monkeypatch
        monkeypatch.setenv("ENVIRONMENT", "staging")

        # Test authenticated URL (should pass)
        authenticated_url = "redis://user:strongpassword123456@redis.staging:6379"
        validator = RedisSecurityValidator()
        result_with_auth = validator.validate_redis_auth(authenticated_url)

        # Assert: Verify authenticated staging validates successfully
        assert result_with_auth["valid"] is True, \
            "Staging should accept authenticated connections"

        # Test unauthenticated URL behavior
        unauthenticated_url = "redis://redis.staging:6379"
        result_without_auth = validator.validate_redis_auth(unauthenticated_url)

        # Verify staging has appropriate validation behavior
        # (Either passes with warning or fails with error, depending on policy)
        assert "valid" in result_without_auth, "Result must have valid key"
        assert "auth_info" in result_without_auth, "Result must have auth_info"

        # Verify clear messaging regardless of validation result
        has_warnings = len(result_without_auth.get("warnings", [])) > 0
        has_errors = len(result_without_auth.get("errors", [])) > 0
        assert has_warnings or has_errors, \
            "Staging should provide feedback about missing authentication"
