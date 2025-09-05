#!/usr/bin/env python3
"""
Aggressive DuckDB Database Cleanup Script

This script removes ALL tables except the essential ones:
- doc_registry
- saved_queries  
- saved_reports

Usage:
    python3 aggressive_cleanup.py
"""

import duckdb
import os
from typing import List

def get_all_tables_except_essential(conn: duckdb.DuckDBPyConnection) -> List[str]:
    """
    Get all tables except the essential ones to keep
    
    Args:
        conn: DuckDB connection
        
    Returns:
        List of table names to remove
    """
    try:
        # Get all tables from the database
        result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'")
        all_tables = [row[0] for row in result.fetchall()]
        
        # Essential tables to keep
        essential_tables = {'doc_registry', 'saved_queries', 'saved_reports'}
        
        # Find tables that are NOT in the essential list
        tables_to_remove = [table for table in all_tables if table not in essential_tables]
        
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
    Main aggressive cleanup function
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
        
        # Get tables to remove (all except essential)
        tables_to_remove = get_all_tables_except_essential(conn)
        
        if not tables_to_remove:
            print("No tables found to remove (only essential tables present)")
            return
        
        print(f"\nTables to remove ({len(tables_to_remove)}):")
        for table in tables_to_remove:
            print(f"  - {table}")
        
        # Confirm removal
        print(f"\n⚠️  WARNING: This will remove {len(tables_to_remove)} tables!")
        print("Only keeping: doc_registry, saved_queries, saved_reports")
        print("Proceeding with aggressive cleanup...")
        
        # Remove the tables
        removed_count = remove_tables(conn, tables_to_remove)
        
        # Get final table count
        result = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'main'")
        final_count = result.fetchone()[0]
        
        print(f"\nAggressive cleanup completed:")
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
        print("\n✅ Aggressive database cleanup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during aggressive cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
