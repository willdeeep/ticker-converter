# Deployment Guide

## Overview

This guide covers the setup and deployment of the ticker-converter SQL-centric ETL pipeline for NYSE stock market data analysis. The system uses PostgreSQL as the single database solution for both development and production environments.

## Prerequisites

### System Requirements
- Python 3.9+ 
- Git
- PostgreSQL 12+ (development and production)
- Apache Airflow 3.0.4+ (optional for orchestration)

### API Access
- Alpha Vantage API key (free tier available)
- Currency conversion API access (exchangerate-api.com or similar)

## Development Setup

### 1. Repository Setup
```bash
git clone https://github.com/willdeeep/ticker-converter.git
cd ticker-converter
```

### 2. Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Dependencies Installation
```bash
# Core dependencies
pip install -e .

# Development tools
pip install -e ".[dev]"

# All features
pip install -e ".[all]"
```

### 4. PostgreSQL Database Setup

#### Option 1: Local PostgreSQL Installation
```bash
# macOS (using Homebrew)
brew install postgresql
brew services start postgresql

# Create database
createdb ticker_converter

# Create user (optional)
psql -c "CREATE USER ticker_user WITH PASSWORD 'your_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE ticker_converter TO ticker_user;"
```

#### Option 2: Docker PostgreSQL
```bash
# Run PostgreSQL in Docker
docker run --name ticker-postgres \
  -e POSTGRES_DB=ticker_converter \
  -e POSTGRES_USER=ticker_user \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  -d postgres:14

# Wait for container to start
sleep 10
```

### 5. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
CURRENCY_API_KEY=your_currency_api_key
DATABASE_URL=postgresql://ticker_user:your_password@localhost:5432/ticker_converter
```

### 6. Database Schema Initialization
```bash
# Create database schema using SQL scripts
psql $DATABASE_URL -f sql/ddl/001_create_dimensions.sql
psql $DATABASE_URL -f sql/ddl/002_create_facts.sql
psql $DATABASE_URL -f sql/ddl/003_create_views.sql
psql $DATABASE_URL -f sql/ddl/004_create_indexes.sql

# Or run the setup script
python scripts/setup_database.py
```

# Verify schema creation
python -c "from src.ticker_converter.database.connection import get_database_connection; print('Database connected successfully')"
```

### 6. Development Server
```bash
# Start FastAPI development server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Verify API endpoints
curl http://localhost:8000/docs
```

## Production Deployment

### 1. PostgreSQL Setup
```bash
# Install PostgreSQL (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE ticker_converter;
CREATE USER ticker_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ticker_converter TO ticker_user;
\q
```

### 2. Production Environment
```bash
# Production environment variables
export DATABASE_URL=postgresql://ticker_user:secure_password@localhost:5432/ticker_converter
export ALPHA_VANTAGE_API_KEY=your_production_key
export CURRENCY_API_KEY=your_production_key
export ENVIRONMENT=production
```

### 3. Database Migration
```bash
# Run schema creation on PostgreSQL
python scripts/setup_database.py --production

# Verify production database
python -c "
from src.ticker_converter.database.connection import get_database_connection
conn = get_database_connection()
print('Production database connected successfully')
conn.close()
"
```

### 4. Application Deployment

#### Option A: Direct Deployment
```bash
# Install production dependencies
pip install gunicorn

# Start production server
gunicorn api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

#### Option B: Docker Deployment
```bash
# Build Docker image
docker build -t ticker-converter .

# Run container
docker run -d \
    --name ticker-converter \
    -p 8000:8000 \
    -e DATABASE_URL=postgresql://ticker_user:password@host.docker.internal:5432/ticker_converter \
    -e ALPHA_VANTAGE_API_KEY=your_key \
    ticker-converter
```

### 5. Reverse Proxy Setup (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Airflow Orchestration Setup

### 1. Airflow Installation
```bash
# Install Airflow 3.0.4 with PostgreSQL provider
pip install "apache-airflow>=3.0.4[postgres]"

# Initialize Airflow database
airflow db init

# Create admin user
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

### 2. DAG Deployment
```bash
# Copy DAGs to Airflow directory
cp dags/*.py $AIRFLOW_HOME/dags/

# Start Airflow services
airflow webserver --port 8080 &
airflow scheduler &
```

### 3. Database Connections
```bash
# Add database connection in Airflow UI
# Connection ID: warehouse_db
# Connection Type: PostgreSQL
# Host: localhost
# Database: ticker_converter
# Username: ticker_user
# Password: secure_password
```

## Monitoring and Maintenance

### 1. Health Checks
```bash
# API health check
curl http://localhost:8000/health

# Database connectivity
python scripts/data_validation.py --check-connection

# Data freshness validation
python scripts/data_validation.py --check-freshness
```

### 2. Log Management
```bash
# Application logs location
tail -f logs/ticker-converter.log

# Airflow logs
tail -f $AIRFLOW_HOME/logs/scheduler/latest/*.log
```

### 3. Database Maintenance
```sql
-- Check table sizes
SELECT 
    tablename, 
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
FROM pg_tables 
WHERE schemaname = 'public';

-- Data retention (keep last 90 days)
DELETE FROM fact_stock_prices 
WHERE date_id IN (
    SELECT date_id FROM dim_dates 
    WHERE date < CURRENT_DATE - INTERVAL '90 days'
);
```

## Performance Tuning

### 1. Database Optimization
```sql
-- Update table statistics
ANALYZE fact_stock_prices;
ANALYZE fact_currency_rates;

-- Rebuild indexes
REINDEX INDEX idx_stock_prices_date_stock;
REINDEX INDEX idx_currency_rates_date;
```

### 2. Application Configuration
```python
# Database connection pooling
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 30
SQLALCHEMY_POOL_TIMEOUT = 30
```

## Backup and Recovery

### 1. Database Backup
```bash
# PostgreSQL backup
pg_dump ticker_converter > backup_$(date +%Y%m%d).sql

# Automated daily backup
0 2 * * * /usr/bin/pg_dump ticker_converter > /backups/daily_$(date +\%Y\%m\%d).sql
```

### 2. Data Recovery
```bash
# Restore from backup
psql ticker_converter < backup_20250811.sql

# Verify data integrity
python scripts/data_validation.py --full-check
```

## Troubleshooting

### Common Issues

**Database Connection Errors**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify connection string
python -c "import os; print(os.getenv('DATABASE_URL'))"
```

**API Response Errors**:
```bash
# Check application logs
tail -f logs/api.log

# Test database queries directly
python scripts/data_validation.py --test-queries
```

**Airflow DAG Failures**:
```bash
# Check DAG status
airflow dags state nyse_stock_etl 2025-08-11

# View task logs
airflow tasks log nyse_stock_etl fetch_stock_data 2025-08-11
```

### Performance Issues
- Monitor query execution times in database logs
- Check index usage with EXPLAIN ANALYZE
- Verify API response cache configuration
- Monitor system resources (CPU, memory, disk I/O)

## Security Considerations

### 1. API Security
- Implement proper API key rotation
- Use HTTPS in production
- Configure rate limiting
- Validate all input parameters

### 2. Database Security
- Use connection pooling with authentication
- Implement read-only user for API queries
- Regular security updates for PostgreSQL
- Network isolation for database access

### 3. Environment Security
- Store secrets in environment variables
- Use secure secret management systems
- Regular dependency updates
- Access logging and monitoring

This deployment guide provides a complete setup process for both development and production environments, ensuring reliable operation of the NYSE stock market data analytics pipeline.
