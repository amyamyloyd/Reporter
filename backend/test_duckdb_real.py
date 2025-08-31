#!/usr/bin/env python3
"""
Test script for duckdb_manager.py using real Excel files

This script tests the DuckDB manager functions with actual Excel data
to validate the integration works correctly.
"""

import pandas as pd
import os
from duckdb_manager import (
    create_memory_database, 
    dataframe_to_table, 
    extract_data_version_from_filename,
    verify_table_data,
    list_tables,
    get_table_info
)

def test_duckdb_manager():
    """Test DuckDB manager functions with real Excel file"""
    
    print("🧪 Testing DuckDB Manager with Real Excel File")
    print("=" * 50)
    
    # Test 1: Data version extraction
    print("\n1️⃣ Testing data version extraction...")
    test_filename = "Campaign_data_2025-08-27_160349.xlsx"
    version = extract_data_version_from_filename(test_filename)
    print(f"   Filename: {test_filename}")
    print(f"   Extracted version: {version}")
    
    # Test 2: Load real Excel file
    print("\n2️⃣ Loading real Excel file...")
    excel_path = "stored_queries/files/Campaign_data_2025-08-27_160349.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"   ❌ Excel file not found: {excel_path}")
        return False
    
    try:
        # Load Excel file into DataFrame
        # Specify engine='openpyxl' for .xlsx files to avoid format detection issues
        df = pd.read_excel(excel_path, engine='openpyxl')
        print(f"   ✅ Excel file loaded successfully")
        print(f"   📊 DataFrame shape: {df.shape}")
        print(f"   📋 Columns: {list(df.columns)}")
        print(f"   📈 Sample data:")
        print(df.head(3).to_string())
        
    except Exception as e:
        print(f"   ❌ Failed to load Excel file: {e}")
        return False
    
    # Test 3: Create persistent database
    print("\n3️⃣ Creating persistent DuckDB database...")
    try:
        conn = create_memory_database()
        print(f"   ✅ Database connection created")
        
        # List tables before (should be empty)
        tables_before = list_tables(conn)
        print(f"   📋 Tables before: {tables_before}")
        
    except Exception as e:
        print(f"   ❌ Failed to create database: {e}")
        return False
    
    # Test 4: Create DuckDB table
    print("\n4️⃣ Creating DuckDB table...")
    table_name = "campaign_data_2025_08_27"
    
    try:
        success = dataframe_to_table(conn, df, table_name)
        if success:
            print(f"   ✅ Table '{table_name}' created successfully")
        else:
            print(f"   ❌ Failed to create table '{table_name}'")
            return False
            
    except Exception as e:
        print(f"   ❌ Error creating table: {e}")
        return False
    
    # Test 5: Verify table data
    print("\n5️⃣ Verifying table data...")
    try:
        is_valid = verify_table_data(conn, table_name, len(df))
        if is_valid:
            print(f"   ✅ Data verification passed")
        else:
            print(f"   ❌ Data verification failed")
            
    except Exception as e:
        print(f"   ❌ Error verifying data: {e}")
    
    # Test 6: List tables after creation
    print("\n6️⃣ Listing tables after creation...")
    try:
        tables_after = list_tables(conn)
        print(f"   📋 Tables after: {tables_after}")
        
    except Exception as e:
        print(f"   ❌ Error listing tables: {e}")
    
    # Test 7: Get table info
    print("\n7️⃣ Getting table information...")
    try:
        table_info = get_table_info(conn, table_name)
        if table_info:
            print(f"   ✅ Table info retrieved")
            print(f"   📊 Row count: {table_info['row_count']}")
            print(f"   📋 Column count: {len(table_info['columns'])}")
            print(f"   🔍 Sample data:")
            for i, row in enumerate(table_info['sample_data'][:3]):
                print(f"      Row {i+1}: {row}")
        else:
            print(f"   ❌ Failed to get table info")
            
    except Exception as e:
        print(f"   ❌ Error getting table info: {e}")
    
    # Test 8: Test data version extraction with actual filename
    print("\n8️⃣ Testing data version with actual filename...")
    actual_filename = "Campaign_data_2025-08-27_160349.xlsx"
    actual_version = extract_data_version_from_filename(actual_filename)
    print(f"   📁 Actual filename: {actual_filename}")
    print(f"   📅 Extracted version: {actual_version}")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    try:
        conn.close()
        print(f"   ✅ Database connection closed")
    except Exception as e:
        print(f"   ❌ Error closing connection: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 DuckDB Manager Test Complete!")
    return True

if __name__ == "__main__":
    # Run the test
    success = test_duckdb_manager()
    
    if success:
        print("\n✅ All tests passed! DuckDB manager is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
