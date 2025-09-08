#!/usr/bin/env python3
"""
Create Airflow admin user for Airflow 3.0+
"""
import os
import sys
import sqlite3


def create_admin_user_sql():
    """Create admin user using direct SQL approach"""
    
    # Get credentials from environment
    username = os.getenv('AIRFLOW_ADMIN_USERNAME', 'admin')
    password = os.getenv('AIRFLOW_ADMIN_PASSWORD', 'admin')
    email = os.getenv('AIRFLOW_ADMIN_EMAIL', 'admin@localhost')
    first_name = os.getenv('AIRFLOW_ADMIN_FIRSTNAME', 'Admin')
    last_name = os.getenv('AIRFLOW_ADMIN_LASTNAME', 'User')
    
    db_path = os.path.join(os.getenv('AIRFLOW_HOME', './airflow'), 'airflow.db')
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM ab_user WHERE username = ?", (username,))
        if cursor.fetchone():
            print(f"Admin user '{username}' already exists")
            conn.close()
            return True
        
        # Get the Admin role ID
        cursor.execute("SELECT id FROM ab_role WHERE name = 'Admin'")
        admin_role = cursor.fetchone()
        if not admin_role:
            print("Error: Admin role not found. Database may not be properly initialized.")
            conn.close()
            return False
        
        admin_role_id = admin_role[0]
        
        # Hash the password (simple approach for now)
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash(password)
        
        # Insert the user
        cursor.execute("""
            INSERT INTO ab_user (username, first_name, last_name, email, password, active, created_on, changed_on)
            VALUES (?, ?, ?, ?, ?, 1, datetime('now'), datetime('now'))
        """, (username, first_name, last_name, email, password_hash))
        
        user_id = cursor.lastrowid
        
        # Assign Admin role to user
        cursor.execute("""
            INSERT INTO ab_user_role (user_id, role_id)
            VALUES (?, ?)
        """, (user_id, admin_role_id))
        
        conn.commit()
        conn.close()
        
        print(f"Successfully created admin user: {username}")
        return True
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False


if __name__ == "__main__":
    success = create_admin_user_sql()
    sys.exit(0 if success else 1)
