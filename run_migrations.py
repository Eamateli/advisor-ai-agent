#!/usr/bin/env python3
"""
Database Migration Runner
This script runs the Alembic migrations to create all database tables.
"""

import os
import sys
import subprocess
import psycopg2
from psycopg2 import sql

def check_database_connection():
    """Check if we can connect to the database"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/financial_advisor_agent')
        conn = psycopg2.connect(database_url)
        conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def run_migrations():
    """Run Alembic migrations"""
    try:
        print("🔄 Running database migrations...")
        
        # Change to backend directory
        os.chdir('backend')
        
        # Run alembic upgrade
        result = subprocess.run(['alembic', 'upgrade', 'head'], 
                              capture_output=True, text=True, check=True)
        
        print("✅ Migrations completed successfully")
        print("Migration output:")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        print("Error output:")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_tables():
    """Verify that tables were created"""
    try:
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/financial_advisor_agent')
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Get list of tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        
        print("\n📋 Database tables created:")
        for table in tables:
            print(f"  ✅ {table[0]}")
        
        # Check for specific required tables
        required_tables = ['users', 'chat_messages', 'documents', 'embeddings']
        existing_tables = [table[0] for table in tables]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            print(f"\n⚠️  Missing required tables: {missing_tables}")
            return False
        else:
            print(f"\n✅ All required tables present!")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def main():
    print("🚀 Starting Database Migration Process")
    print("=" * 50)
    
    # Step 1: Check database connection
    if not check_database_connection():
        print("❌ Cannot proceed without database connection")
        return False
    
    # Step 2: Run migrations
    if not run_migrations():
        print("❌ Migration failed")
        return False
    
    # Step 3: Verify tables
    if not verify_tables():
        print("❌ Table verification failed")
        return False
    
    print("\n🎉 Database setup completed successfully!")
    print("You can now use the chat application.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
