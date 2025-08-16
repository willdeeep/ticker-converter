# SQL Infrastructure Documentation

## Overview
This directory contains all SQL files for the ticker-converter project. All SQL queries are executed by Airflow DAGs, centralized in this location for better organization and maintainability.

## Related Documentation

### Architecture Documentation
- **[Database Schema & Operations](../../docs/architecture/database_schema_and_operations.md)** - Complete database schema design, normalization strategy, and operational procedures
- **[ETL Pipeline Implementation](../../docs/architecture/etl_pipeline_implementation.md)** - Detailed ETL pipeline guide with SQL transformation architecture and data flow
- **[Airflow Setup & Architecture](../../docs/architecture/airflow_setup.md)** - Airflow 3.0.4 configuration and SQL-centric workflow orchestration

### Project Documentation
- **[SQL Infrastructure Audit Report](../../my_docs/SQL_INFRASTRUCTURE_AUDIT_REPORT.md)** - Complete audit of SQL consolidation and infrastructure organization
- **[Refactoring Project Status](../../my_docs/TEMP-REFACTORING-PROJECT.md)** - Current project progress and testing coverage strategy

## Directory Structure

```
dags/sql/
├── ddl/          # Data Definition Language (Schema Creation)
├── etl/          # Extract, Transform, Load Operations  
├── queries/      # Business Logic Queries
└── README.md     # This documentation
```

## DDL Files (Schema Management)
- `001_create_dimensions.sql` - Create dimension tables (stocks, currencies, dates)
- `002_create_facts.sql` - Create fact tables (stock prices, exchange rates)
- `003_create_views.sql` - Create analytical views
- `004_create_indexes.sql` - Create performance indexes

## ETL Files (Data Pipeline Operations)
- `load_raw_stock_data_to_postgres.sql` - Load raw stock data from API to staging
- `load_raw_exchange_data_to_postgres.sql` - Load raw exchange rate data
- `clean_transform_data.sql` - Data cleaning and transformation logic
- `daily_transforms.sql` - Daily data transformation processes
- `load_dimensions.sql` - Load dimension table data
- `load_stock_dimension.sql` - Load stock dimension specifically
- `load_currency_dimension.sql` - Load currency dimension specifically  
- `load_date_dimension.sql` - Load date dimension specifically
- `data_quality_checks.sql` - Data validation and quality checks
- `cleanup_old_data.sql` - Remove outdated data

## Query Files (Business Logic)
- `top_performers.sql` - Identify top performing stocks
- `magnificent_seven_top_performers.sql` - Performance metrics for major tech stocks
- `magnificent_seven_performance_details.sql` - Detailed performance analysis
- `stock_summary.sql` - Stock summary statistics
- `price_ranges.sql` - Price range analysis
- `currency_conversion.sql` - Currency conversion utilities

## Usage in DAGs

### Configuration
DAGs reference SQL files using the `SQL_DIR` configuration:
```python
SQL_DIR = "dags/sql"
```

### File References
SQL files are referenced relative to the DAGs directory:
```python
SQL_FILES = {
    "load_raw_stock_data": "sql/etl/load_raw_stock_data_to_postgres.sql",
    "data_quality_checks": "sql/etl/data_quality_checks.sql",
    # ...
}
```

## Naming Conventions

### File Naming
- **DDL**: `000_verb_object.sql` (numbered for execution order)
- **ETL**: `verb_object_action.sql` (descriptive action names)
- **Queries**: `object_purpose.sql` (business-focused names)

### Content Standards
- Include header comment describing purpose
- Use parameterized queries with `{{ ds }}` for date templating
- Include example usage in comments
- Follow SQL formatting standards (uppercase keywords, consistent indentation)

## Maintenance

### Adding New SQL Files
1. Place in appropriate subdirectory (ddl/etl/queries)
2. Follow naming conventions
3. Update DAG configuration if referenced
4. Add documentation to this README

### Removing SQL Files
1. Check for DAG references before deletion
2. Update DAG configuration
3. Remove from this documentation

### Migration Notes
- **August 15, 2025**: Consolidated from separate `sql/` directory to centralize all SQL in `dags/sql/`
- All duplicates removed, structure standardized
- DAG configurations updated to use new paths

## Troubleshooting

### Common Issues
- **Template Not Found**: Check SQL file path in DAG configuration
- **Permission Errors**: Ensure SQL files are readable by Airflow process
- **Syntax Errors**: Validate SQL syntax before deployment

### Validation
Test DAG parsing after SQL changes:
```bash
airflow dags report | grep daily_etl_dag
```
