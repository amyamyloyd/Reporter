#!/usr/bin/env python3
"""
DuckDB Database Cleanup Script

This script removes tables matching specific patterns from the DuckDB database:
- Tables starting with 'test'
- Tables starting with 'financial'
- Tables starting with 'hotel'
- Tables starting with 'excel_data'
- Tables starting with 'Hospital'
- Tables starting with 'employees'
- Tables starting with 'campaign'

Usage:
    python3 cleanup_duckdb.py
"""

import duckdb
import os
import re
from typing import List

def get_tables_to_remove(conn: duckdb.DuckDBPyConnection) -> List[str]:
    """
    Get list of tables that match the cleanup patterns
    
    Args:
        conn: DuckDB connection
        
    Returns:
        List of table names to remove
    """
    try:
        # Get all tables from the database
        result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'")
        all_tables = [row[0] for row in result.fetchall()]
        
        # Define patterns to match for removal
        patterns = [
            r'^test',           # Tables starting with 'test'
            r'^financial',      # Tables starting with 'financial'
            r'^hotel',          # Tables starting with 'hotel'
            r'^excel_data',     # Tables starting with 'excel_data'
            r'^Hospital',       # Tables starting with 'Hospital'
            r'^employees',      # Tables starting with 'employees'
            r'^campaign'        # Tables starting with 'campaign'
        ]
        
        # Find tables matching any of the patterns
        tables_to_remove = []
        for table_name in all_tables:
            for pattern in patterns:
                if re.match(pattern, table_name, re.IGNORECASE):
                    tables_to_remove.append(table_name)
                    break  # Only add once even if multiple patterns match
        
        return tables_to_remove
        
    except Exception as e:
        print(f"Error getting tables to remove: {e}")
        return []

def remove_tables(conn: duckdb.DuckDBPyConnection, table_names: List[str]) -> int:
    """
    Remove specified tables from the database
    
    Args:
        conn: DuckDB connection
        table_names: List of table names to remove
        
    Returns:
        Number of tables successfully removed
    """
    removed_count = 0
    
    for table_name in table_names:
        try:
            # Drop the table
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            print(f"✅ Removed table: {table_name}")
            removed_count += 1
            
        except Exception as e:
            print(f"❌ Failed to remove table '{table_name}': {e}")
    
    return removed_count

def main():
    """
    Main cleanup function
    """
    try:
        # Connect to the database
        db_path = os.path.join(os.getcwd(), 'excel_reporting.db')
        print(f"Connecting to database: {db_path}")
        
        conn = duckdb.connect(db_path)
        
        # Get current table count
        result = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'main'")
        initial_count = result.fetchone()[0]
        print(f"Initial table count: {initial_count}")
        
        # Get tables to remove
        tables_to_remove = get_tables_to_remove(conn)
        
        if not tables_to_remove:
            print("No tables found matching cleanup patterns")
            return
        
        print(f"\nTables to remove ({len(tables_to_remove)}):")
        for table in tables_to_remove:
            print(f"  - {table}")
        
        # Confirm removal
        print(f"\nProceeding to remove {len(tables_to_remove)} tables...")
        
        # Remove the tables
        removed_count = remove_tables(conn, tables_to_remove)
        
        # Get final table count
        result = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'main'")
        final_count = result.fetchone()[0]
        
        print(f"\nCleanup completed:")
        print(f"  - Tables removed: {removed_count}")
        print(f"  - Initial count: {initial_count}")
        print(f"  - Final count: {final_count}")
        
        # Show remaining tables
        if final_count > 0:
            print(f"\nRemaining tables:")
            result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'")
            remaining_tables = [row[0] for row in result.fetchall()]
            for table in remaining_tables:
                print(f"  - {table}")
        
        conn.close()
        print("\n✅ Database cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
