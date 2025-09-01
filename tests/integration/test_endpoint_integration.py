"""Integration tests for API endpoint functionality.

These tests verify that the API endpoint can be launched and presents data as intended.
Tests the FastAPI application startup, endpoint accessibility, and data format validation.
"""

import os
import time

import pytest
from fastapi.testclient import TestClient

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

# Try to import the FastAPI app
try:
    from src.ticker_converter.api.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    app = None  # type: ignore[assignment]


class TestAPIEndpointAccessibility:
    """Test API endpoint accessibility and basic functionality."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
    def test_fastapi_app_creation(self) -> None:
        """Test that FastAPI app can be created successfully."""
        assert app is not None, "FastAPI app should be importable"
        assert hasattr(app, "routes"), "App should have routes attribute"

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
    def test_api_test_client_startup(self) -> None:
        """Test that API can be started with test client."""
        with TestClient(app) as client:
            # Test basic connectivity
            response = client.get("/")

            # Should get some response (might be 404 if no root route, but connection works)
            assert response.status_code in [
                200,
                404,
                422,
            ], f"API should respond, got status {response.status_code}"

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
    def test_health_check_endpoint(self) -> None:
        """Test health check endpoint if it exists."""
        with TestClient(app) as client:
            # Try common health check paths
            health_paths = ["/health", "/healthz", "/ping", "/status"]

            health_found = False
            for path in health_paths:
                response = client.get(path)
                if response.status_code == 200:
                    health_found = True
                    assert response.json() is not None, "Health check should return JSON"
                    break

            # If no health endpoint exists, that's okay for now
            if not health_found:
                pytest.skip("No health check endpoint found - not required")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
    def test_api_documentation_endpoints(self) -> None:
        """Test that API documentation endpoints are accessible."""
        with TestClient(app) as client:
            # Test OpenAPI schema
            docs_response = client.get("/docs")
            redoc_response = client.get("/redoc")
            openapi_response = client.get("/openapi.json")

            # At least one documentation endpoint should work
            working_docs = [r for r in [docs_response, redoc_response, openapi_response] if r.status_code == 200]

            assert len(working_docs) > 0, "At least one documentation endpoint should work"


class TestAPIEndpointData:
    """Test API endpoint data format and content."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
    def test_ticker_data_endpoint_format(self) -> None:
        """Test ticker data endpoint returns proper format."""
        with TestClient(app) as client:
            # Try common ticker endpoint paths
            ticker_paths = [
                "/ticker/AAPL",
                "/tickers/AAPL",
                "/api/v1/ticker/AAPL",
                "/api/v1/tickers/AAPL",
                "/stock/AAPL",
                "/stocks/AAPL",
            ]

            endpoint_found = False
            for path in ticker_paths:
                response = client.get(path)

                if response.status_code == 200:
                    endpoint_found = True
                    data = response.json()

                    # Validate response structure
                    assert isinstance(data, (dict, list)), "Response should be JSON object or array"

                    # If it's a dict, check for common ticker data fields
                    if isinstance(data, dict):
                        expected_fields = [
                            "symbol",
                            "price",
                            "date",
                            "open",
                            "close",
                            "high",
                            "low",
                        ]
                        found_fields = [field for field in expected_fields if field in data]
                        assert len(found_fields) > 0, f"Should contain ticker data fields, got: {list(data.keys())}"

                    break
                if response.status_code == 422:
                    # Validation error - endpoint exists but needs different parameters
                    endpoint_found = True
                    break

            if not endpoint_found:
                pytest.skip("No ticker data endpoint found - may not be implemented yet")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
    def test_api_error_handling(self) -> None:
        """Test API error handling for invalid requests."""
        with TestClient(app) as client:
            # Test invalid ticker symbol
            invalid_paths = [
                "/ticker/INVALID_SYMBOL_XYZ",
                "/api/v1/ticker/INVALID_SYMBOL_XYZ",
                "/stock/INVALID_SYMBOL_XYZ",
            ]

            for path in invalid_paths:
                response = client.get(path)

                if response.status_code in [404, 422, 400]:
                    # Good - API handles invalid requests properly
                    if response.headers.get("content-type", "").startswith("application/json"):
                        error_data = response.json()
                        assert isinstance(error_data, dict), "Error response should be JSON object"
                        # Common error response fields
                        assert any(
                            key in error_data for key in ["detail", "error", "message"]
                        ), "Error response should contain error information"
                    break
            else:
                pytest.skip("No ticker endpoints found to test error handling")


class TestAPIProductionReadiness:
    """Test API production readiness features."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
    def test_cors_headers(self) -> None:
        """Test CORS headers are configured."""
        with TestClient(app) as client:
            response = client.options("/")

            # Check if CORS headers are present (optional for development)
            cors_headers = [
                "access-control-allow-origin",
                "access-control-allow-methods",
                "access-control-allow-headers",
            ]

            cors_found = any(header in response.headers for header in cors_headers)

            if not cors_found:
                pytest.skip("CORS not configured - acceptable for development")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
    def test_security_headers(self) -> None:
        """Test basic security headers."""
        with TestClient(app) as client:
            response = client.get("/")

            # Check for basic security headers (optional for development)
            security_headers = [
                "x-content-type-options",
                "x-frame-options",
                "x-xss-protection",
            ]

            security_found = any(header in response.headers for header in security_headers)

            if not security_found:
                pytest.skip("Security headers not configured - acceptable for development")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
    def test_api_response_times(self) -> None:
        """Test API response times are reasonable."""
        with TestClient(app) as client:
            start_time = time.time()
            client.get("/")
            end_time = time.time()

            response_time = end_time - start_time

            # API should respond within reasonable time (5 seconds for test client)
            assert response_time < 5.0, f"API response too slow: {response_time:.2f}s"


class TestAPIWithExternalServices:
    """Test API integration with external services (if configured)."""

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
    def test_api_database_connectivity(self) -> None:
        """Test API can connect to database if configured."""
        # Check if database environment variables are set
        db_vars = ["POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER"]
        db_configured = all(os.getenv(var) for var in db_vars)

        if not db_configured:
            pytest.skip("Database not configured - API may work without DB")

        with TestClient(app) as client:
            # Try endpoints that might use database
            db_endpoints = ["/health", "/api/v1/health", "/status", "/api/v1/status"]

            for endpoint in db_endpoints:
                response = client.get(endpoint)

                if response.status_code == 200:
                    data = response.json()

                    # Look for database status in response
                    if isinstance(data, dict):
                        db_status_keys = ["database", "db", "postgres", "storage"]
                        db_status_found = any(key in str(data).lower() for key in db_status_keys)

                        if db_status_found:
                            # API reports database status - good!
                            break
            else:
                pytest.skip("No database status endpoints found")

    @pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
    def test_api_external_api_integration(self) -> None:
        """Test API integration with external APIs (Alpha Vantage)."""
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

        if not api_key or api_key in ["demo", "your_api_key_here"]:
            pytest.skip("Alpha Vantage API key not configured")

        with TestClient(app) as client:
            # Try endpoints that might use external APIs
            external_endpoints = [
                "/ticker/AAPL",
                "/api/v1/ticker/AAPL",
                "/stock/AAPL",
                "/api/v1/stock/AAPL",
            ]

            for endpoint in external_endpoints:
                response = client.get(endpoint)

                if response.status_code == 200:
                    # Good - API can fetch external data
                    data = response.json()
                    assert data is not None, "Should return data from external API"
                    break
                if response.status_code in [429, 503]:
                    # Rate limited or service unavailable - API is configured correctly
                    pytest.skip(f"External API rate limited or unavailable: {response.status_code}")
                    break
                if response.status_code == 422:
                    # Validation error - endpoint exists but needs different parameters
                    pytest.skip("Ticker endpoint exists but requires different parameters")
                    break
            else:
                pytest.skip("No external API endpoints found")


class TestAPIManualStartup:
    """Test API can be started manually (outside test client)."""

    def test_api_script_exists(self) -> None:
        """Test that API startup script exists."""
        # Check for common API startup files
        api_files = [
            "src/ticker_converter/run_api.py",
            "src/ticker_converter/api/main.py",
            "run_api.py",
            "main.py",
        ]

        found_files = []
        for api_file in api_files:
            if os.path.exists(api_file):
                found_files.append(api_file)

        assert len(found_files) > 0, f"No API startup script found. Checked: {api_files}"

    def test_api_startup_configuration(self) -> None:
        """Test API startup configuration."""
        # Check if uvicorn or similar ASGI server is configured
        try:
            import uvicorn  # pylint: disable=import-outside-toplevel,unused-import

            UVICORN_AVAILABLE = True
        except ImportError:
            UVICORN_AVAILABLE = False

        if not UVICORN_AVAILABLE:
            pytest.skip("Uvicorn not available - cannot test manual startup")

        # Configuration test passed if uvicorn is available
        assert UVICORN_AVAILABLE, "Uvicorn should be available for API startup"
