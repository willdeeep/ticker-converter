# DAGs Directory

## Purpose
Contains all Apache Airflow DAG Python scripts for orchestrating data pipeline workflows. This directory serves as the single source of truth for all scheduled data operations and ETL processes.

## Directory Structure

### `/dags/` Directory

**Git Status**: Tracked  
**Use Case**: Airflow DAG definitions and workflow orchestration

This directory contains Airflow DAGs for orchestrating data pipeline workflows.

## Directory Structure
```
dags/
├── README.md                      # This file
├── daily_etl_dag.py              # Daily ETL workflow DAG
├── test_etl_dag.py               # ETL testing DAG
├── __pycache__/                  # Python bytecode cache
├── raw_data/                     # Raw data staging area
└── sql/                          # SQL scripts for DAG operations
```
- **Contents**: 
  - Primary DAG files (e.g., `daily_etl_dag.py`, `test_etl_dag.py`)
  - DAG configuration and scheduling logic
  - Task definitions and dependencies

### `/dags/sql/`
- **Use Case**: All SQL queries used throughout the project including:
  - Database initialization and schema creation (DDL)
  - Data cleaning and transformation (ETL)
  - Data validation queries
  - API endpoint data selection queries
  - DAG-specific SQL operations
- **Git Status**: Tracked
- **Sub-directories**:
  - `ddl/`: Database schema and table creation
  - `etl/`: Data transformation and cleaning queries
  - `queries/`: Data selection and analysis queries

### `/dags/raw_data/`
- **Use Case**: Temporary storage for raw data files during DAG execution
- **Git Status**: Untracked (excluded via .gitignore)
- **Contents**: Downloaded data files, temporary processing files

## Organization Principles

1. **Clean DAG Design**: DAGs should be readable and maintainable by separating business logic into subfolder modules
2. **SQL Centralization**: All SQL queries live in `/dags/sql/` regardless of whether they're used by DAGs, CLI, or API endpoints
3. **Function Separation**: Python helper functions for DAGs are organized in appropriate subfolders by functionality
4. **No Hardcoded Values**: Configuration and data should come from external sources, not embedded in DAG files

## Usage Guidelines

- **New DAGs**: Place main DAG files directly in `/dags/` root
- **New SQL**: Add to appropriate `/dags/sql/` subdirectory based on purpose
- **Helper Functions**: Create organized subfolders for reusable DAG components
- **Documentation**: Each DAG should have clear docstrings explaining purpose, schedule, and dependencies

## Integration Points

- **Airflow Runtime**: DAGs are loaded by Airflow scheduler from this directory
- **CLI Integration**: Functions in `/src/` may reference SQL files in `/dags/sql/`
- **API Integration**: API endpoints in `/api/` use queries from `/dags/sql/`
- **Database Operations**: All database schema and operations defined here
