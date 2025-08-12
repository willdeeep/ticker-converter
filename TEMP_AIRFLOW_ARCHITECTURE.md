# Airflow Management Architecture Documentation

## Overview

This document details the Airflow management system implemented following the unified CLI→Orchestrator→Manager→Service architectural pattern.

## Architecture Flow

```
Makefile Commands → CLI (cli_ingestion.py) → Orchestrator → AirflowManager → Airflow Services
```

## Components

### 1. AirflowManager (`src/ticker_converter/data_ingestion/airflow_manager.py`)

**Purpose**: Handles all Apache Airflow lifecycle operations including setup, teardown, and monitoring.

**Key Features**:
- Environment-driven configuration using `.env` variables
- Process management with PID tracking
- Service status monitoring
- Graceful shutdown capabilities
- Comprehensive error handling and logging

**Main Methods**:

#### Setup Operations
- `initialize_airflow_database()`: Initialize Airflow metadata database (uses `airflow db migrate`)
- `create_admin_user()`: Create admin user from environment configuration
- `start_webserver()`: Start Airflow webserver on specified port
- `start_scheduler()`: Start Airflow scheduler in background
- `setup_airflow_complete()`: Complete setup workflow (database + user + services)

#### Teardown Operations
- `stop_airflow_services()`: Stop all Airflow processes (webserver and scheduler)
- `teardown_airflow()`: Complete teardown workflow

#### Monitoring Operations
- `get_airflow_status()`: Get current service status and running processes

### 2. Orchestrator Integration (`src/ticker_converter/data_ingestion/orchestrator.py`)

**Added Methods**:
- `perform_airflow_setup()`: Orchestrates complete Airflow setup
- `perform_airflow_teardown()`: Orchestrates Airflow service shutdown
- `get_airflow_status()`: Retrieves Airflow status information

### 3. CLI Commands (`src/ticker_converter/cli_ingestion.py`)

**New Commands**:
- `--airflow-setup`: Initialize database, create user, start services
- `--airflow-teardown`: Stop all Airflow services
- `--airflow-status`: Check service status and running processes

**Command Functions**:
- `airflow_setup_command()`: User-friendly setup with access information
- `airflow_teardown_command()`: Safe service shutdown
- `airflow_status_command()`: Status reporting

### 4. Makefile Integration

**New Targets**:
- `make airflow`: Complete Airflow setup (replaces old manual commands)
- `make airflow-stop`: Stop all services
- `make airflow-status`: Check service status

## Configuration

### Environment Variables (`.env` file)

```bash
# Airflow Configuration
AIRFLOW_ADMIN_USERNAME=admin1@test.local
AIRFLOW_ADMIN_PASSWORD=test123
AIRFLOW_ADMIN_EMAIL=admin1@test.local
AIRFLOW_ADMIN_FIRSTNAME=Admin
AIRFLOW_ADMIN_LASTNAME=User
```

### Airflow Home
- Default: `~/airflow`
- Configurable via `AIRFLOW_HOME` environment variable

## Usage Examples

### Setup Airflow
```bash
# Via Makefile
make airflow

# Via CLI directly
python -m ticker_converter.cli_ingestion --airflow-setup
```

### Stop Services
```bash
# Via Makefile
make airflow-stop

# Via CLI directly
python -m ticker_converter.cli_ingestion --airflow-teardown
```

### Check Status
```bash
# Via Makefile
make airflow-status

# Via CLI directly
python -m ticker_converter.cli_ingestion --airflow-status
```

## Process Management

### Service Detection
- Uses `ps aux` to find running Airflow processes
- Identifies webserver and scheduler by command line patterns
- Tracks PIDs for proper process management

### Graceful Shutdown
- Sends SIGTERM to processes for graceful shutdown
- Provides feedback on stopped services
- Handles cases where services are already stopped

## Error Handling

### Database Issues
- Handles Airflow configuration problems
- Provides detailed error messages for troubleshooting
- Continues with available operations when possible

### Service Management
- Gracefully handles missing processes
- Timeout protection for long-running operations
- Clear error reporting for failed operations

## Testing Results

### ✅ Successful Operations
1. **Service Status**: Correctly identifies running webserver/scheduler
2. **Service Teardown**: Successfully stopped scheduler (PID: 96796)
3. **Makefile Integration**: All commands work through proper architecture
4. **Environment Configuration**: Uses `.env` variables correctly

### 🔧 Known Issues
1. **Airflow 3.0 Compatibility**: Some configuration module issues with newer Airflow versions
2. **Auth Manager**: Configuration issues with `airflow.auth.managers.fab.fab_auth_manager.FabAuthManager`

## Benefits

### Architectural Consistency
- Follows same pattern as database operations
- Centralized logic in manager classes
- Proper separation of concerns

### Maintainability
- All Airflow operations in single manager class
- Comprehensive logging throughout stack
- Clear error handling and user feedback

### Flexibility
- Can start/stop services individually or together
- Environment-driven configuration
- Easy to extend for additional Airflow operations

## Future Enhancements

1. **DAG Management**: Add DAG deployment and management capabilities
2. **Health Monitoring**: Enhanced health checks and monitoring
3. **Configuration Management**: Dynamic Airflow configuration management
4. **Integration**: Better integration with data pipeline orchestration
