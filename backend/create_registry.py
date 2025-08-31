#!/usr/bin/env python3
"""
One-time script to create the doc_registry table in DuckDB
Run this once manually to set up the registry structure
"""
import os
import sys

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from duckdb_manager import create_memory_database, create_document_registry_table

def main():
    """Create the document registry table once"""
    print("Creating document registry table...")
    
    try:
        # Create database connection
        conn = create_memory_database()
        print("✅ Connected to DuckDB database")
        
        # Create the registry table structure (no sample data)
        success = create_document_registry_table(conn)
        
        if success:
            print("✅ Document registry table created successfully")
            print("✅ Registry is now empty and ready for manual population")
        else:
            print("❌ Failed to create document registry table")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
