#!/usr/bin/env python3
"""
Simple table creator - just load Excel file and create DuckDB table
Bypasses all the complex upload logic to test basic functionality
"""

import duckdb
import pandas as pd
import os

def create_simple_table():
    """Create a simple table from the existing Excel file"""
    
    # Path to the existing Excel file (relative to backend directory)
    # Use a working Excel file from the root directory
    excel_file = "../Campaign_data.xlsx"
    
    # Check if file exists
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        return False
    
    print(f"📁 Found Excel file: {excel_file}")
    
    try:
        # Load Excel data
        print("🔄 Loading Excel data...")
        df = pd.read_excel(excel_file, engine='openpyxl')
        print(f"✅ Loaded data: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Create DuckDB connection
        print("🔄 Creating DuckDB connection...")
        db_path = os.path.join(os.path.dirname(__file__), 'excel_reporting.db')
        print(f"🗄️  Database path: {db_path}")
        
        conn = duckdb.connect(db_path)
        print("✅ DuckDB connection created")
        
        # Create simple table name
        table_name = "test_table"
        print(f"🔄 Creating table: {table_name}")
        
        # Drop table if exists
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        print("✅ Dropped existing table")
        
        # Create table from DataFrame using DuckDB's proper method
        # First register the DataFrame as a temporary view
        conn.register('temp_df', df)
        print("✅ DataFrame registered as temporary view")
        
        # Now create table from the registered view
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_df")
        print("✅ Table created successfully")
        
        # Clean up the temporary view
        conn.unregister('temp_df')
        print("✅ Temporary view cleaned up")
        
        # Verify table
        result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = result.fetchone()[0]
        print(f"✅ Table verified: {row_count} rows")
        
        # Show table info
        result = conn.execute(f"DESCRIBE {table_name}")
        columns = result.fetchall()
        print(f"📋 Table structure:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
        
        # Close connection
        conn.close()
        print("✅ Database connection closed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting simple table creation...")
    success = create_simple_table()
    
    if success:
        print("🎉 SUCCESS: Table created!")
    else:
        print("💥 FAILED: Table creation failed")
