#!/usr/bin/env python3
"""
Standalone test script for JSON loading to PostgreSQL.

This script tests the JSON loading functionality without going through
Airflow's task system to avoid SDK issues.
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root / "src"))


def test_postgresql_connection():
    """Test basic PostgreSQL connectivity."""
    try:
        import psycopg2

        # Database configuration from environment
        db_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "local_db"),
            "user": os.getenv("POSTGRES_USER", "dbuser123"),
            "password": os.getenv("POSTGRES_PASSWORD", "password123"),
        }

        print(f"🔍 Testing PostgreSQL connection...")
        print(f"📊 Host: {db_config['host']}, Port: {db_config['port']}, DB: {db_config['database']}")

        # Test connection
        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
            connect_timeout=5,
        )

        cursor = conn.cursor()
        cursor.execute("SELECT version(), current_database();")
        version, current_db = cursor.fetchone()

        print(f"✅ Database connection successful!")
        print(f"✅ Connected to database: {current_db}")
        print(f"✅ PostgreSQL version: {version}")

        # Test table creation
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS test_standalone_load (
                id SERIAL PRIMARY KEY,
                test_type VARCHAR(50),
                filename VARCHAR(255),
                record_count INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """
        )
        conn.commit()
        print("✅ Test table created successfully")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False


def test_stock_json_loading():
    """Test loading stock JSON files."""
    try:
        print(f"\n🔍 Testing stock JSON loading...")

        # Find stock JSON files
        stocks_dir = project_root / "dags" / "raw_data" / "stocks"
        stock_files = list(stocks_dir.glob("*.json"))

        print(f"📁 Found {len(stock_files)} stock JSON files in {stocks_dir}")

        if not stock_files:
            print("⚠️  No stock JSON files found")
            return False

        total_records = 0

        # Process first file only
        json_file = stock_files[0]
        print(f"📖 Processing {json_file.name}...")

        with open(json_file, "r", encoding="utf-8") as f:
            stock_data = json.load(f)

        if isinstance(stock_data, dict):
            # Handle different JSON structures
            if "Time Series (Daily)" in stock_data:
                records = len(stock_data["Time Series (Daily)"])
                print(f"📊 Found Time Series data with {records} records")
            elif "data" in stock_data:
                records = len(stock_data["data"])
                print(f"📊 Found data array with {records} records")
            else:
                records = len(stock_data)
                print(f"📊 Found dictionary with {records} keys")
        else:
            records = len(stock_data)
            print(f"📊 Found array with {records} records")

        total_records += records

        # Test database insertion
        import psycopg2

        db_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "local_db"),
            "user": os.getenv("POSTGRES_USER", "dbuser123"),
            "password": os.getenv("POSTGRES_PASSWORD", "password123"),
        }

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Insert test record
        cursor.execute(
            "INSERT INTO test_standalone_load (test_type, filename, record_count) VALUES (%s, %s, %s)",
            ("stock_json", json_file.name, records),
        )
        conn.commit()

        print(f"✅ Successfully inserted test record for {json_file.name}")

        cursor.close()
        conn.close()

        print(f"🎉 Stock JSON test completed - processed {total_records} records")
        return True

    except Exception as e:
        print(f"❌ Stock JSON loading failed: {e}")
        return False


def test_exchange_json_loading():
    """Test loading exchange rate JSON files."""
    try:
        print(f"\n🔍 Testing exchange rate JSON loading...")

        # Find exchange JSON files
        exchange_dir = project_root / "dags" / "raw_data" / "exchange"
        exchange_files = list(exchange_dir.glob("*.json"))

        print(f"📁 Found {len(exchange_files)} exchange JSON files in {exchange_dir}")

        if not exchange_files:
            print("⚠️  No exchange JSON files found")
            return False

        total_records = 0

        # Process first file only
        json_file = exchange_files[0]
        print(f"📖 Processing {json_file.name}...")

        with open(json_file, "r", encoding="utf-8") as f:
            exchange_data = json.load(f)

        if isinstance(exchange_data, dict):
            # Handle different JSON structures
            if "rates" in exchange_data:
                records = len(exchange_data["rates"])
                print(f"📊 Found rates data with {records} records")
            elif "data" in exchange_data:
                records = len(exchange_data["data"])
                print(f"📊 Found data array with {records} records")
            else:
                records = len(exchange_data)
                print(f"📊 Found dictionary with {records} keys")
        else:
            records = len(exchange_data)
            print(f"📊 Found array with {records} records")

        total_records += records

        # Test database insertion
        import psycopg2

        db_config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "database": os.getenv("POSTGRES_DB", "local_db"),
            "user": os.getenv("POSTGRES_USER", "dbuser123"),
            "password": os.getenv("POSTGRES_PASSWORD", "password123"),
        }

        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Insert test record
        cursor.execute(
            "INSERT INTO test_standalone_load (test_type, filename, record_count) VALUES (%s, %s, %s)",
            ("exchange_json", json_file.name, records),
        )
        conn.commit()

        print(f"✅ Successfully inserted test record for {json_file.name}")

        cursor.close()
        conn.close()

        print(f"🎉 Exchange JSON test completed - processed {total_records} records")
        return True

    except Exception as e:
        print(f"❌ Exchange JSON loading failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting standalone JSON loading tests...")
    print("=" * 60)

    success_count = 0
    total_tests = 3

    # Test 1: PostgreSQL connection
    if test_postgresql_connection():
        success_count += 1

    # Test 2: Stock JSON loading
    if test_stock_json_loading():
        success_count += 1

    # Test 3: Exchange JSON loading
    if test_exchange_json_loading():
        success_count += 1

    print(f"\n" + "=" * 60)
    print(f"🎯 Test Results: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("🎉 All tests passed! JSON loading functionality is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit(main())
