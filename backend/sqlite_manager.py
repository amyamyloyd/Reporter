# DuckDB database operations for Phase 1
# ONLY handle DuckDB database operations

import duckdb
import pandas as pd
from typing import Optional, List, Dict, Any
import re

def create_memory_database() -> duckdb.DuckDBPyConnection:
    """
    Create in-memory DuckDB connection for session
    
    Returns:
        DuckDB connection object
    """
    try:
        # Create in-memory DuckDB connection
        conn = duckdb.connect(':memory:')
        return conn
    except Exception as e:
        print(f"Failed to create DuckDB database: {e}")
        raise

def dataframe_to_table(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame, table_name: str) -> bool:
    """
    Convert pandas DataFrame to DuckDB table using df.to_sql()
    
    Args:
        conn: DuckDB connection
        df: DataFrame to convert
        table_name: Name for the DuckDB table
        
    Returns:
        bool: Success status
    """
    try:
        # Validate table name (DuckDB safe)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            print(f"Invalid table name: {table_name}")
            return False
            
        # Convert DataFrame to DuckDB table
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df")
        
        # Verify table was created
        result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = result.fetchone()[0]
        
        if row_count == len(df):
            print(f"Successfully created table '{table_name}' with {row_count} rows")
            return True
        else:
            print(f"Table created but row count mismatch: expected {len(df)}, got {row_count}")
            return False
            
    except Exception as e:
        print(f"Error creating table {table_name}: {e}")
        return False

def get_table_info(conn: duckdb.DuckDBPyConnection, table_name: str) -> Optional[dict]:
    """
    Get detailed information about a table
    
    Args:
        conn: DuckDB connection
        table_name: Name of the table
        
    Returns:
        dict: Table information or None if error
    """
    try:
        # Get table schema information
        result = conn.execute(f"DESCRIBE {table_name}")
        columns = result.fetchall()
        
        # Get row count
        count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = count_result.fetchone()[0]
        
        # Get sample data
        sample_result = conn.execute(f"SELECT * FROM {table_name} LIMIT 5")
        sample_data = sample_result.fetchall()
        
        return {
            "table_name": table_name,
            "columns": [{"name": col[0], "type": col[1]} for col in columns],
            "row_count": row_count,
            "sample_data": sample_data
        }
        
    except Exception as e:
        print(f"Error getting table info for {table_name}: {e}")
        return None

def list_tables(conn: duckdb.DuckDBPyConnection) -> List[str]:
    """
    List all tables in the database
    
    Args:
        conn: DuckDB connection
        
    Returns:
        List of table names
    """
    try:
        # Use DuckDB's information_schema to list tables
        result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'")
        tables = [row[0] for row in result.fetchall()]
        return tables
    except Exception as e:
        print(f"Error listing tables: {e}")
        return []
