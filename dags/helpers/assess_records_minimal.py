"""
Minimal version of assess_records to debug the hanging issue.
"""

from airflow.providers.postgres.hooks.postgres import PostgresHook


def assess_latest_records_minimal() -> dict:
    """Minimal version for debugging."""
    print("🔍 Starting minimal assessment...")
    
    try:
        # Test connection first
        hook = PostgresHook(postgres_conn_id="postgres_default")
        print("✅ Hook created successfully")
        
        # Test simple query
        result = hook.get_first("SELECT 1 as test")
        print(f"✅ Simple query result: {result}")
        
        # Test one table check
        print("🔍 Testing single table check...")
        result = hook.get_first(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'stock_dimension'"
        )
        print(f"✅ Table check result: {result}")
        
        print("✅ Minimal assessment completed")
        return {"status": "success", "test_result": result[0] if result else 0}
        
    except Exception as e:
        print(f"❌ Error in minimal assessment: {e}")
        return {"status": "error", "error": str(e)}
