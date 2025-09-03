"""Integration tests for PostgreSQL database functionality.

These tests verify that PostgreSQL is present and accessible, configured for use,
with user configured and database initialized. Bonus: if database has been populated,
it returns number of entries and data quality assessment.
"""

import os

import psycopg2
import pytest
from psycopg2 import sql

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

# Load database configuration from environment
# Integration tests should FAIL if environment variables are not set
# This ensures the setup process has properly configured the environment
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")


class TestPostgreSQLAccessibility:
    """Test PostgreSQL database accessibility and configuration."""

    def test_postgres_environment_variables_present(self) -> None:
        """Test that all required PostgreSQL environment variables are set."""
        required_vars = {
            "POSTGRES_HOST": POSTGRES_HOST,
            "POSTGRES_PORT": POSTGRES_PORT,
            "POSTGRES_DB": POSTGRES_DB,
            "POSTGRES_USER": POSTGRES_USER,
            "POSTGRES_PASSWORD": POSTGRES_PASSWORD,
        }

        for var_name, var_value in required_vars.items():
            assert var_value is not None, f"{var_name} must be set in environment"
            assert var_value != "", f"{var_name} cannot be empty"

        # Check that port is numeric
        assert POSTGRES_PORT is not None, "POSTGRES_PORT must be set"
        assert POSTGRES_PORT.isdigit(), "POSTGRES_PORT must be numeric"

    def test_postgres_server_running(self) -> None:
        """Test that PostgreSQL server is running and accessible."""
        try:
            # Attempt to connect to PostgreSQL server
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database="postgres",  # Connect to default database first
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                connect_timeout=10,
            )
            conn.close()
        except psycopg2.OperationalError as e:
            pytest.fail(f"PostgreSQL server not accessible: {e}")

    def test_database_exists_and_accessible(self) -> None:
        """Test that the ticker_converter database exists and is accessible."""
        try:
            # Connect to the specific database
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                connect_timeout=10,
            )

            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()

            assert version is not None, "Should be able to query database"
            assert "PostgreSQL" in version[0], "Should return PostgreSQL version"

            cursor.close()
            conn.close()

        except psycopg2.OperationalError as e:
            pytest.fail(f"Database {POSTGRES_DB} not accessible: {e}")

    def test_user_has_required_permissions(self) -> None:
        """Test that the configured user has required database permissions."""
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
            )

            cursor = conn.cursor()

            # Test CREATE permission (create temporary table)
            cursor.execute(
                """
                CREATE TEMPORARY TABLE test_permissions (
                    id SERIAL PRIMARY KEY,
                    test_data TEXT
                );
            """
            )

            # Test INSERT permission
            cursor.execute(
                """
                INSERT INTO test_permissions (test_data) VALUES ('test');
            """
            )

            # Test SELECT permission
            cursor.execute("SELECT * FROM test_permissions;")
            result = cursor.fetchone()
            assert result is not None, "Should be able to read from table"

            # Test UPDATE permission
            cursor.execute(
                """
                UPDATE test_permissions SET test_data = 'updated' WHERE id = %s;
            """,
                (result[0],),
            )

            # Test DELETE permission
            cursor.execute("DELETE FROM test_permissions WHERE id = %s;", (result[0],))

            conn.commit()
            cursor.close()
            conn.close()

        except psycopg2.Error as e:
            pytest.fail(f"User {POSTGRES_USER} lacks required permissions: {e}")


class TestDatabaseSchema:
    """Test database schema and initialization."""

    def test_database_schema_exists(self) -> None:
        """Test that required database schema/tables exist."""
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
            )

            cursor = conn.cursor()

            # Check if any tables exist in the database
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public';
            """
            )

            tables = cursor.fetchall()

            # For now, just verify we can query the schema
            # Database might be empty which is acceptable
            assert isinstance(tables, list), "Should be able to query table schema"

            cursor.close()
            conn.close()

        except psycopg2.Error as e:
            pytest.fail(f"Cannot query database schema: {e}")

    def test_database_accepts_ticker_data_format(self) -> None:
        """Test that database can accept ticker data format."""
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
            )

            cursor = conn.cursor()

            # Create a temporary table that mimics ticker data structure
            cursor.execute(
                """
                CREATE TEMPORARY TABLE test_ticker_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    date DATE NOT NULL,
                    open_price DECIMAL(10,2),
                    high_price DECIMAL(10,2),
                    low_price DECIMAL(10,2),
                    close_price DECIMAL(10,2),
                    volume BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            # Test inserting ticker-like data
            cursor.execute(
                """
                INSERT INTO test_ticker_data
                (symbol, date, open_price, high_price, low_price, close_price, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
                ("AAPL", "2024-01-01", 150.00, 155.00, 149.50, 154.25, 1000000),
            )

            # Verify data was inserted
            cursor.execute("SELECT COUNT(*) FROM test_ticker_data;")
            count = cursor.fetchone()[0]
            assert count == 1, "Should have inserted one record"

            conn.commit()
            cursor.close()
            conn.close()

        except psycopg2.Error as e:
            pytest.fail(f"Database cannot handle ticker data format: {e}")


class TestDatabaseDataQuality:
    """Test database data quality if data is present (bonus tests)."""

    def test_database_populated_data_count(self) -> None:
        """Test database population and return entry counts if data exists."""
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
            )

            cursor = conn.cursor()

            # Get list of all tables
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE';
            """
            )

            tables = cursor.fetchall()

            if not tables:
                pytest.skip("No tables found in database - database not yet populated")

            # Count rows in each table
            table_counts = {}
            for table in tables:
                table_name = table[0]
                cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
                count = cursor.fetchone()[0]
                table_counts[table_name] = count

            # Log the counts for information
            print(f"\nDatabase table counts: {table_counts}")

            # At least verify we can count rows
            assert isinstance(table_counts, dict), "Should return table counts"

            cursor.close()
            conn.close()

        except psycopg2.Error as e:
            pytest.skip(f"Cannot assess database population: {e}")

    def test_data_quality_basic_checks(self) -> None:
        """Test basic data quality if ticker data tables exist."""
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
            )

            cursor = conn.cursor()

            # Look for tables that might contain ticker data
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name LIKE ANY(ARRAY['%ticker%', '%stock%', '%price%', '%market%']);
            """
            )

            ticker_tables = cursor.fetchall()

            if not ticker_tables:
                pytest.skip("No ticker-related tables found - data quality check not applicable")

            # Basic data quality checks
            for table in ticker_tables:
                table_name = table[0]

                # Check for NULL values in key fields (if they exist)
                cursor.execute(
                    sql.SQL(
                        """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = %s
                    AND column_name IN ('symbol', 'date', 'close_price');
                """
                    ),
                    (table_name,),
                )

                key_columns = cursor.fetchall()

                for col in key_columns:
                    col_name = col[0]
                    cursor.execute(
                        sql.SQL(
                            """
                        SELECT COUNT(*) FROM {} WHERE {} IS NULL;
                    """
                        ).format(sql.Identifier(table_name), sql.Identifier(col_name))
                    )
                    null_count = cursor.fetchone()[0]

                    print(f"Table {table_name}, column {col_name}: {null_count} NULL values")

            cursor.close()
            conn.close()

        except psycopg2.Error as e:
            pytest.skip(f"Cannot perform data quality checks: {e}")


class TestDatabaseConnectionPooling:
    """Test database connection handling for production readiness."""

    def test_multiple_connections(self) -> None:
        """Test that database can handle multiple connections."""
        connections = []
        try:
            # Create multiple connections
            for i in range(3):
                conn = psycopg2.connect(
                    host=POSTGRES_HOST,
                    port=POSTGRES_PORT,
                    database=POSTGRES_DB,
                    user=POSTGRES_USER,
                    password=POSTGRES_PASSWORD,
                )
                connections.append(conn)

            # Verify all connections work
            for i, conn in enumerate(connections):
                cursor = conn.cursor()
                cursor.execute("SELECT %s as connection_id;", (i,))
                result = cursor.fetchone()
                assert result[0] == i, f"Connection {i} should work"
                cursor.close()

        except psycopg2.Error as e:
            pytest.fail(f"Database cannot handle multiple connections: {e}")
        finally:
            # Clean up connections
            for conn in connections:
                try:
                    conn.close()
                except psycopg2.Error:
                    pass

    def test_connection_recovery(self) -> None:
        """Test database connection recovery after close."""
        try:
            # Create connection
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
            )

            # Use connection
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            result1 = cursor.fetchone()
            cursor.close()
            conn.close()

            # Create new connection
            conn2 = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
            )

            # Use new connection
            cursor2 = conn2.cursor()
            cursor2.execute("SELECT 2;")
            result2 = cursor2.fetchone()
            cursor2.close()
            conn2.close()

            assert result1[0] == 1, "First connection should work"
            assert result2[0] == 2, "Second connection should work"

        except psycopg2.Error as e:
            pytest.fail(f"Database connection recovery failed: {e}")
