#!/bin/bash
# Airflow CLI wrapper that loads environment variables
# Usage: ./scripts/airflow-cli.sh [airflow command args...]

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Load environment variables
set -a
source .env
set +a

# Execute airflow command with all arguments
exec airflow "$@"
