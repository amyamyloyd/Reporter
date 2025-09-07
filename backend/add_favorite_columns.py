#!/usr/bin/env python3
"""
Script to add is_favorite columns to doc_registry, saved_queries, and saved_reports tables
This script adds the required columns for the SuperMenu favorites functionality
"""
import os
import sys

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from duckdb_manager import create_persistent_database
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_favorite_columns():
    """
    Add is_favorite BOOLEAN DEFAULT false columns to all required tables
    """
    try:
        # Create database connection
        conn = create_persistent_database()
        logger.info("✅ Connected to DuckDB database")
        
        # List of tables and their ALTER statements
        alter_statements = [
            {
                "table": "doc_registry",
                "sql": "ALTER TABLE doc_registry ADD COLUMN is_favorite BOOLEAN DEFAULT false",
                "description": "Add is_favorite column to doc_registry table"
            },
            {
                "table": "saved_queries", 
                "sql": "ALTER TABLE saved_queries ADD COLUMN is_favorite BOOLEAN DEFAULT false",
                "description": "Add is_favorite column to saved_queries table"
            },
            {
                "table": "saved_reports",
                "sql": "ALTER TABLE saved_reports ADD COLUMN is_favorite BOOLEAN DEFAULT false", 
                "description": "Add is_favorite column to saved_reports table"
            }
        ]
        
        # Execute each ALTER statement
        for alter_info in alter_statements:
            try:
                logger.info(f"Executing: {alter_info['description']}")
                conn.execute(alter_info['sql'])
                logger.info(f"✅ Successfully added is_favorite column to {alter_info['table']}")
                
            except Exception as e:
                # Check if column already exists
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    logger.info(f"ℹ️  Column is_favorite already exists in {alter_info['table']}")
                else:
                    logger.error(f"❌ Error adding is_favorite to {alter_info['table']}: {e}")
                    raise
        
        # Verify the changes by checking table schemas
        logger.info("\n🔍 Verifying table schemas...")
        
        for table_name in ["doc_registry", "saved_queries", "saved_reports"]:
            try:
                # Check if table exists
                table_exists = conn.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                """).fetchone()[0]
                
                if table_exists > 0:
                    # Get table schema
                    schema_result = conn.execute(f"DESCRIBE {table_name}").fetchall()
                    has_favorite = any("is_favorite" in str(col) for col in schema_result)
                    
                    if has_favorite:
                        logger.info(f"✅ {table_name}: is_favorite column confirmed")
                    else:
                        logger.warning(f"⚠️  {table_name}: is_favorite column not found")
                else:
                    logger.info(f"ℹ️  {table_name}: table does not exist yet")
                    
            except Exception as e:
                logger.error(f"❌ Error checking {table_name}: {e}")
        
        # Close database connection
        conn.close()
        logger.info("\n✅ Database schema update completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating database schema: {e}")
        return False

def main():
    """Main function to add favorite columns"""
    print("🚀 Adding is_favorite columns to database tables...")
    print("=" * 60)
    
    success = add_favorite_columns()
    
    if success:
        print("\n🎉 SUCCESS: All is_favorite columns added successfully!")
        print("The SuperMenu favorites functionality is now ready to use.")
    else:
        print("\n💥 FAILED: Could not add is_favorite columns")
        print("Please check the error messages above and try again.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
