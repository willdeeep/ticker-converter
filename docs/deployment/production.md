# Production Deployment Guide

## Executive Summary

This guide provides comprehensive instructions for deploying the ticker-converter ETL pipeline to production environments. The deployment strategy emphasizes **reliability**, **scalability**, and **operational excellence** through containerization, infrastructure as code, monitoring, and automated deployment pipelines.

**Production Value Proposition**: Deploy a robust, high-availability stock market data analytics platform capable of handling production workloads with comprehensive monitoring, automated scaling, and disaster recovery capabilities.

## Production Architecture Overview

### Deployment Strategy Decision Matrix

| Component | Technology Choice | Rationale | Production Benefits |
|-----------|------------------|-----------|-------------------|
| **Container Runtime** | Docker + Docker Compose | Consistent environments, easy scaling | Eliminates "works on my machine" issues |
| **Database** | PostgreSQL 15+ | ACID compliance, performance, JSON support | Enterprise-grade reliability and performance |
| **Web Server** | Gunicorn + Uvicorn Workers | Production-grade ASGI server | High concurrency, process management |
| **Reverse Proxy** | Nginx | Static content, load balancing, SSL termination | Performance, security, caching |
| **Process Management** | systemd | Service management, auto-restart | Reliability, logging, resource limits |
| **Monitoring** | Prometheus + Grafana | Metrics collection and visualization | Observability, alerting, performance tracking |
| **Logging** | Structured JSON logs | Centralized logging, searchability | Debugging, audit trails, compliance |

### Production Infrastructure Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx)                    │
│                   SSL Termination • Caching                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│              Application Layer (Docker)                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │   FastAPI App   │ │  Airflow Web    │ │ Airflow Worker  ││
│  │  (Multiple)     │ │    Server       │ │   (Multiple)    ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                Database Layer                                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐│
│  │  PostgreSQL     │ │     Redis       │ │   Monitoring    ││
│  │   Primary       │ │    Cache        │ │  (Prometheus)   ││
│  └─────────────────┘ └─────────────────┘ └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Environment Setup and Requirements

### Production Server Requirements

#### Minimum Hardware Specifications
```yaml
CPU: 4 cores (8 recommended)
RAM: 8GB (16GB recommended)
Storage: 100GB SSD (250GB recommended)
Network: 1Gbps connection
OS: Ubuntu 22.04 LTS or CentOS 8+
```

#### Production Dependencies
```bash
# System packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    docker.io \
    docker-compose-plugin \
    nginx \
    postgresql-client-15 \
    redis-tools \
    certbot \
    python3-certbot-nginx \
    htop \
    iotop \
    netdata
```

### Production Environment Variables

**File: `/opt/ticker-converter/.env.production`**
```bash
# === PRODUCTION ENVIRONMENT CONFIGURATION ===

# Application Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json

# Database Configuration (Primary)
DATABASE_URL=postgresql://ticker_user:${DB_PASSWORD}@db:5432/ticker_converter
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=ticker_converter
POSTGRES_USER=ticker_user
POSTGRES_PASSWORD=${DB_PASSWORD}

# Database Configuration (Read Replica - Optional)
DATABASE_READ_URL=postgresql://ticker_reader:${DB_READ_PASSWORD}@db-replica:5432/ticker_converter

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# API Keys (from secure vault)
ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}
ALPHA_VANTAGE_RATE_LIMIT=5
ALPHA_VANTAGE_TIMEOUT=30

# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_MAX_REQUESTS=1000
API_MAX_REQUESTS_JITTER=50
API_TIMEOUT=30

# Airflow Configuration
AIRFLOW_HOME=/opt/airflow
AIRFLOW_UID=50000
AIRFLOW_GID=0
AIRFLOW__CORE__DAGS_FOLDER=/opt/airflow/dags
AIRFLOW__CORE__LOAD_EXAMPLES=false
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql://airflow_user:${AIRFLOW_DB_PASSWORD}@db:5432/airflow
AIRFLOW__CORE__FERNET_KEY=${AIRFLOW_FERNET_KEY}
AIRFLOW__WEBSERVER__SECRET_KEY=${AIRFLOW_SECRET_KEY}
AIRFLOW__WEBSERVER__AUTHENTICATE=true
AIRFLOW__WEBSERVER__AUTH_BACKEND=airflow.api.auth.backend.basic_auth

# Airflow Admin User
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=${AIRFLOW_ADMIN_PASSWORD}
AIRFLOW_ADMIN_EMAIL=admin@ticker-converter.com
AIRFLOW_ADMIN_FIRSTNAME=Admin
AIRFLOW_ADMIN_LASTNAME=User

# Security Configuration
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Monitoring and Metrics
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# SSL Configuration (for HTTPS)
SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem

# Backup Configuration
BACKUP_SCHEDULE="0 2 * * *"
BACKUP_RETENTION_DAYS=30
BACKUP_S3_BUCKET=ticker-converter-backups
```

This comprehensive production deployment guide provides enterprise-grade setup with proper security, monitoring, backup strategies, and operational excellence practices. The configuration supports high availability, scalability, and maintainability required for production environments.

---

**Last Updated**: August 2025 | **Version**: 2.0.0 | **Target**: Production Enterprise Deployment
