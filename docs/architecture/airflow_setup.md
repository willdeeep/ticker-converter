# Apache Airflow 3.0.4 Setup and Architecture

## Executive Summary

The ticker-converter leverages **Apache Airflow 3.0.4** with modern @dag decorator syntax to orchestrate SQL-centric ETL workflows for financial market data processing. This setup prioritizes **SQL operators over Python operators** to align with the project's database-first architecture philosophy, providing reliable workflow orchestration with comprehensive monitoring and error handling.

**Airflow Value Proposition**: By utilizing Airflow's mature orchestration capabilities with SQL-focused operators, the system delivers production-ready workflow management with minimal Python complexity and maximum operational reliability.

## Airflow 3.0.4 Migration Rationale

### Why Upgrade to Airflow 3.0.4

**Modern Syntax Benefits**:
- **@dag Decorators**: Cleaner, more readable DAG definitions with reduced boilerplate code
- **@task Decorators**: Simplified task creation with automatic dependency inference
- **Type Safety**: Better integration with modern Python type hints and mypy static analysis
- **Code Organization**: Improved separation of configuration and business logic

**Performance Improvements**:
- **Task Execution**: Faster task startup and execution times
- **Scheduler Performance**: Enhanced scheduler efficiency for complex DAG dependencies
- **Database Operations**: Improved metadata database performance and connection handling
- **Web UI**: Responsive web interface with better user experience

**Operational Excellence**:
- **Security**: Enhanced security features and authentication mechanisms
- **Monitoring**: Improved logging, metrics, and observability features
- **Configuration**: Simplified configuration management with better defaults
- **Documentation**: Comprehensive documentation and migration guides

### Breaking Changes from Legacy Airflow

**Syntax Migration**:
- **DAG Instantiation**: Old `DAG()` constructor → New `@dag` decorator
- **Task Creation**: Old `PythonOperator` → New `@task` decorator
- **Default Arguments**: Integrated into `@dag` decorator parameters
- **Task Dependencies**: Automatic inference from function calls

**Configuration Changes**:
- **Authentication**: New authentication manager system (FabAuthManager)
- **Database**: Enhanced metadata database schema and migration requirements
- **Environment Variables**: Updated environment variable naming conventions
- **Plugin System**: New plugin architecture with improved loading mechanisms

## DAG Architecture Design

### SQL-First Orchestration Philosophy

**Decision Rationale**: Maximize use of `SQLExecuteQueryOperator` and minimize custom Python operators to align with the project's database-centric architecture.

**Benefits of SQL Operators**:
- **Performance**: Direct database execution without Python processing overhead
- **Maintainability**: SQL logic is version-controlled in external .sql files
- **Debugging**: Easier to test and debug SQL operations independently
- **Scalability**: PostgreSQL optimizations handle data processing more efficiently than Python

### Modern DAG Structure Pattern

```python
# dags/daily_etl_dag.py - Airflow 3.0.4 Implementation
from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

@dag(
    dag_id='daily_market_data_pipeline',
    description='SQL-centric ETL for NYSE stocks and currency data',
    schedule='0 18 * * 1-5',  # 6 PM EST, weekdays only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={
        'owner': 'data-engineering',
        'depends_on_past': False,
        'email_on_failure': True,
        'email_on_retry': False,
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
    },
    tags=['finance', 'etl', 'sql-first', 'v1.1.0']
)
def market_data_pipeline():
    """
    Modern Airflow 3.0.4 DAG implementing SQL-centric ETL pipeline.
    
    Features:
    - @dag decorator for clean configuration
    - SQL operators for all transformations
    - Minimal Python for API ingestion only
    - External .sql files for version control
    """
```

### Task Design Patterns

#### Python Tasks: API Ingestion Only
```python
@task(task_id='extract_stock_data')
def fetch_stock_data():
    """
    Python task limited to external API interaction.
    No business logic - pure data ingestion.
    """
    from ticker_converter.data_ingestion.orchestrator import Orchestrator
    
    orchestrator = Orchestrator()
    result = orchestrator.run_stock_data_ingestion()
    
    # Return metadata for downstream tasks
    return {
        'symbols_processed': result.get('symbols_count', 0),
        'records_ingested': result.get('records_count', 0),
        'execution_time': result.get('duration_seconds', 0)
    }

@task(task_id='extract_currency_rates')
def fetch_currency_data():
    """
    Python task for currency API integration.
    Focused solely on data retrieval.
    """
    from ticker_converter.data_ingestion.orchestrator import Orchestrator
    
    orchestrator = Orchestrator()
    result = orchestrator.run_currency_data_ingestion()
    
    return {
        'rates_processed': result.get('rates_count', 0),
        'api_source': result.get('source', 'unknown')
    }
```

#### SQL Tasks: All Business Logic
```python
# SQL-only transformation tasks using external files
load_dimensions = PostgresOperator(
    task_id='load_dimensions',
    postgres_conn_id='postgres_default',
    sql='sql/etl/load_dimensions.sql',
    hook_params={'application_name': 'airflow_etl'}
)

daily_transform = PostgresOperator(
    task_id='daily_transform',
    postgres_conn_id='postgres_default', 
    sql='sql/etl/daily_transform.sql',
    hook_params={'application_name': 'airflow_etl'}
)

data_quality_checks = PostgresOperator(
    task_id='data_quality_checks',
    postgres_conn_id='postgres_default',
    sql='sql/etl/data_quality_checks.sql',
    hook_params={'application_name': 'airflow_etl'}
)

refresh_views = PostgresOperator(
    task_id='refresh_views',
    postgres_conn_id='postgres_default',
    sql='sql/etl/refresh_analytical_views.sql',
    hook_params={'application_name': 'airflow_etl'}
)
```

#### Task Dependencies: Linear Pipeline
```python
# Clean, readable dependency chain
[fetch_stock_data(), fetch_currency_data()] >> load_dimensions
load_dimensions >> daily_transform >> data_quality_checks >> refresh_views

# Return the DAG instance
dag_instance = market_data_pipeline()
```

## SQL Operator vs Python Operator Strategy

### When to Use SQL Operators

**Data Transformations**:
- Dimensional table loading and updates
- Fact table calculations and aggregations
- Data quality validation queries
- View refresh and materialization operations

**Benefits**:
- **Performance**: Leverage PostgreSQL's query optimization
- **Version Control**: SQL files tracked in Git with proper diff visibility
- **Testing**: SQL can be tested independently in any PostgreSQL client
- **Expertise**: SQL skills are more widely available than complex Python ETL

### When to Use Python Tasks

**External System Integration**:
- API calls to Alpha Vantage, currency services
- File system operations and data validation
- Complex error handling and retry logic
- Configuration and environment management

**Anti-Patterns to Avoid**:
- Data transformations in Python that could be done in SQL
- Complex business logic in Python operators
- Database operations using pandas instead of SQL
- Custom operators when standard SQL operators suffice

## Configuration and Environment Setup

### Airflow Configuration (`airflow.cfg`)

```ini
[core]
# Core Airflow settings optimized for SQL-centric workflows
dags_folder = /path/to/ticker-converter/dags
sql_alchemy_conn = postgresql://airflow_user:password@localhost/airflow_db
executor = LocalExecutor
parallelism = 16
max_active_runs_per_dag = 1

[webserver]
web_server_port = 8080
authenticate = True
auth_backend = airflow.auth.backends.session

[scheduler]
catchup_by_default = False
max_tis_per_query = 512
job_heartbeat_sec = 5

[database]
# PostgreSQL optimizations
sql_alchemy_pool_size = 10
sql_alchemy_max_overflow = 20
sql_alchemy_pool_recycle = 3600
```

### Environment Variables (`.env`)

```bash
# Airflow Core Configuration
AIRFLOW_HOME=/path/to/ticker-converter/airflow
AIRFLOW__CORE__DAGS_FOLDER=/path/to/ticker-converter/dags
AIRFLOW__CORE__EXECUTOR=LocalExecutor

# Database Configuration
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql://airflow_user:password@localhost/airflow_db

# Security Configuration  
AIRFLOW__WEBSERVER__SECRET_KEY=your-secret-key-here
AIRFLOW__WEBSERVER__AUTHENTICATE=True

# Admin User Configuration
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=admin123
AIRFLOW_ADMIN_EMAIL=admin@ticker-converter.local
AIRFLOW_ADMIN_FIRSTNAME=Admin
AIRFLOW_ADMIN_LASTNAME=User

# PostgreSQL Connection for ETL
AIRFLOW_CONN_POSTGRES_DEFAULT=postgresql://willhuntleyclarke@localhost:5432/ticker_converter
```

### Database Connection Setup

```python
# Connection configuration for PostgreSQL operations
from airflow.models import Connection
from airflow import settings

def create_postgres_connection():
    """Create PostgreSQL connection for ETL operations."""
    session = settings.Session()
    
    conn = Connection(
        conn_id='postgres_default',
        conn_type='postgres',
        host='localhost',
        schema='ticker_converter',
        login='willhuntleyclarke',
        port=5432,
        extra=json.dumps({
            'application_name': 'airflow_etl',
            'connect_timeout': 30,
            'sslmode': 'prefer'
        })
    )
    
    session.merge(conn)
    session.commit()
    session.close()
```

## Setup and Deployment Process

### Initial Setup Commands

```bash
# 1. Initialize Airflow database
airflow db init

# 2. Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@ticker-converter.local \
    --password admin123

# 3. Create PostgreSQL connection
python -c "from setup_airflow_conn import create_postgres_connection; create_postgres_connection()"

# 4. Start services
airflow webserver --port 8080 --daemon
airflow scheduler --daemon
```

### Makefile Integration

```makefile
# Simplified Airflow management through Make
.PHONY: airflow airflow-stop airflow-status

airflow: ## Start Airflow services (webserver + scheduler)
	@echo "Starting Apache Airflow 3.0.4..."
	@airflow db migrate
	@airflow webserver --port 8080 --daemon
	@airflow scheduler --daemon
	@echo "Airflow available at http://localhost:8080"
	@echo "   Username: admin | Password: admin123"

airflow-stop: ## Stop all Airflow services
	@echo "Stopping Airflow services..."
	@pkill -f "airflow webserver" || true
	@pkill -f "airflow scheduler" || true
	@echo "Airflow services stopped"

airflow-status: ## Check Airflow service status
	@echo "Airflow Service Status:"
	@ps aux | grep -E "(airflow webserver|airflow scheduler)" | grep -v grep || echo "No Airflow processes running"
```

## Monitoring and Troubleshooting

### DAG Monitoring Best Practices

**Web UI Monitoring**:
- **Task Duration**: Monitor execution times for performance regression
- **Failure Rates**: Track task failure patterns and retry behavior
- **Data Quality**: Review data quality check results in task logs
- **Resource Usage**: Monitor memory and CPU usage for optimization

**Logging Configuration**:
```python
# Enhanced logging for SQL operations
import logging
from airflow.configuration import conf

# Configure detailed SQL logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('airflow.providers.postgres').setLevel(logging.DEBUG)
```

### Common Issues and Solutions

#### DAG Import Errors
**Symptoms**: DAGs not appearing in web UI
**Diagnosis**: Check `airflow dags list` and logs for import errors
**Solutions**:
- Verify Python path includes project root
- Check DAG syntax with `python dags/daily_etl_dag.py`
- Review scheduler logs for detailed error messages

#### SQL Operator Failures
**Symptoms**: PostgreSQL tasks failing with connection errors
**Diagnosis**: Test connection with `airflow connections test postgres_default`
**Solutions**:
- Verify PostgreSQL service is running
- Check connection configuration in Airflow admin
- Test SQL files independently in PostgreSQL client

#### Performance Issues
**Symptoms**: Slow task execution or scheduler lag
**Diagnosis**: Review task duration trends and database query performance
**Solutions**:
- Optimize SQL queries in external .sql files
- Adjust `sql_alchemy_pool_size` for better connection management
- Consider task parallelism adjustments

### Advanced Monitoring Setup

```python
# Custom monitoring task for pipeline health
@task(task_id='pipeline_health_check')
def monitor_pipeline_health():
    """Monitor overall pipeline health and performance."""
    from ticker_converter.monitoring import PipelineMonitor
    
    monitor = PipelineMonitor()
    metrics = monitor.collect_pipeline_metrics()
    
    # Alert on anomalies
    if metrics['data_freshness_hours'] > 24:
        raise AirflowException("Data freshness exceeds threshold")
    
    if metrics['error_rate_percent'] > 5:
        raise AirflowException("Error rate exceeds threshold")
    
    return metrics
```

## Future Enhancement Roadmap

### Short-Term Improvements (3-6 months)
- **Dynamic DAG Generation**: Create DAGs programmatically for new data sources
- **Advanced Alerting**: Integration with Slack/email for comprehensive notifications
- **Performance Metrics**: Custom metrics collection and visualization
- **Environment Promotion**: Automated DAG deployment across dev/staging/prod

### Medium-Term Evolution (6-12 months)
- **Kubernetes Deployment**: Container-based Airflow deployment for scalability
- **Data Lineage**: Comprehensive data lineage tracking across all transformations
- **Multi-Tenancy**: Support for multiple environments and data pipelines
- **Advanced Scheduling**: Complex scheduling logic with external triggers

### Long-Term Vision (1-2 years)
- **Real-Time Integration**: Stream processing integration with Kafka/Pulsar
- **ML Pipeline**: Machine learning model training and deployment orchestration
- **Governance**: Data governance and compliance automation
- **Federation**: Multi-cluster Airflow federation for global deployments

## Related Documentation

- [Data Pipeline Architecture](data_pipeline.md) - End-to-end pipeline design and SQL transformation logic
- [Database Design](database_design.md) - PostgreSQL schema and optimization strategies
- [Technology Choices](technology_choices.md) - Airflow selection rationale and alternatives analysis
- [Local Setup](../deployment/local_setup.md) - Development environment configuration
- [CLI Usage](../user_guides/cli_usage.md) - Command-line interface for Airflow operations

---

**Last Updated**: August 2025 | **Version**: 1.1.0 | **Airflow Version**: 3.0.4
