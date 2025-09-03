# `/api/` Directory

**Git Status**: Tracked
**Use Case**: FastAPI application and HTTP interface definitions

This directory contains FastAPI application setup, route definitions, and HTTP-specific components.

## Directory Structure
```
api/
├── README.md                      # This file
├── __init__.py                   # Package initialization
├── main.py                       # FastAPI application instance
├── models.py                     # Pydantic models for API requests/responses
├── database.py                   # Database connection and session management
└── dependencies.py               # FastAPI dependency injection components
```

## Purpose
Contains all Python classes for both external API connections (clients) and internal API endpoint definitions (FastAPI server). This directory manages all API-related functionality organized by use case and integration type.

### Current Structure Analysis
Based on existing files:
- **FastAPI Server**: `main.py`, `models.py`, `database.py`, `dependencies.py`
- **External API Clients**: Currently located in `/src/ticker_converter/api_clients/`

### Recommended Organization

#### `/api/server/` (Internal API Endpoints)
- **Use Case**: FastAPI application providing REST endpoints
- **Git Status**: Tracked
- **Contents**:
  - `main.py`: FastAPI application setup and routing
  - `models.py`: Pydantic models for API request/response
  - `database.py`: Database connection and session management
  - `dependencies.py`: Dependency injection for endpoints
  - `endpoints/`: Sub-directory for endpoint modules by domain

#### `/api/clients/` (External API Integration)
- **Use Case**: Classes for connecting to external APIs (Alpha Vantage, etc.)
- **Git Status**: Tracked
- **Contents**: Client classes, authentication, request handling
- **Note**: Currently in `/src/ticker_converter/api_clients/` - may need migration

## Organization Principles

1. **Separation of Concerns**: Clear distinction between serving APIs (server) and consuming APIs (clients)
2. **Domain Organization**: Group related endpoints and clients by business domain
3. **Reusability**: API components should be usable by DAGs, CLI, and other modules
4. **Configuration**: Environment-based API keys and endpoint configuration
5. **Error Handling**: Comprehensive error handling for network operations

## Usage Guidelines

- **New External Clients**: Add to `/api/clients/` with clear interface definitions
- **New Endpoints**: Add to `/api/server/endpoints/` organized by domain
- **Authentication**: Centralize API key and authentication management
- **Documentation**: Auto-generated OpenAPI documentation for FastAPI endpoints
- **Testing**: Comprehensive testing for both client and server functionality

## Integration Points

- **DAG Usage**: DAGs in `/dags/` call API clients for data fetching
- **CLI Integration**: CLI commands in `/src/` use API clients for operations
- **Database Queries**: Server endpoints use SQL queries from `/dags/sql/`
- **Frontend Integration**: API server provides endpoints for external consumption

## Development Guidelines

- **Async Support**: Use async/await patterns for non-blocking operations
- **Rate Limiting**: Implement proper rate limiting for external API calls
- **Caching**: Cache responses where appropriate to reduce API calls
- **Monitoring**: Log API calls and response times for monitoring
- **Documentation**: Clear docstrings and OpenAPI specifications
