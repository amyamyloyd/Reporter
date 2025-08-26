"""
SQLite database operations for Phase 1
ONLY handle SQLite database operations
DO NOT add query logic or agent interactions
"""
import sqlite3
import pandas as pd
from typing import Optional


def create_memory_database() -> sqlite3.Connection:
    """
    Create in-memory SQLite connection for session
    
    Returns:
        SQLite connection object
    """
    try:
        # Create in-memory database
        conn = sqlite3.connect(':memory:')
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Set timeout for busy database
        conn.execute("PRAGMA busy_timeout = 30000")
        
        return conn
        
    except Exception as e:
        print(f"Error creating database: {e}")
        raise


def dataframe_to_table(conn: sqlite3.Connection, df: pd.DataFrame, table_name: str) -> bool:
    """
    Convert pandas DataFrame to SQLite table using df.to_sql()
    
    Args:
        conn: SQLite connection
        df: Pandas DataFrame to convert
        table_name: Name for the SQLite table
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate table name (SQLite safe)
        if not table_name.replace('_', '').isalnum():
            raise ValueError(f"Invalid table name: {table_name}")
        
        # Convert DataFrame to SQLite table
        df.to_sql(
            name=table_name,
            con=conn,
            if_exists='replace',  # Replace if exists
            index=False,  # Don't include DataFrame index
            method='multi'  # Use multi-insert for better performance
        )
        
        # Verify table was created
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        
        if cursor.fetchone():
            print(f"Successfully created table: {table_name}")
            return True
        else:
            print(f"Failed to create table: {table_name}")
            return False
            
    except Exception as e:
        print(f"Error creating table {table_name}: {e}")
        return False


def get_table_info(conn: sqlite3.Connection, table_name: str) -> Optional[dict]:
    """
    Get basic information about a table
    
    Args:
        conn: SQLite connection
        table_name: Name of the table
        
    Returns:
        Dict with table info or None if error
    """
    try:
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        return {
            "table_name": table_name,
            "columns": [{"name": col[1], "type": col[2], "not_null": col[3], "primary_key": col[5]} for col in columns],
            "row_count": row_count
        }
        
    except Exception as e:
        print(f"Error getting table info for {table_name}: {e}")
        return None


def list_tables(conn: sqlite3.Connection) -> list:
    """
    List all tables in the database
    
    Args:
        conn: SQLite connection
        
    Returns:
        List of table names
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        return tables
        
    except Exception as e:
        print(f"Error listing tables: {e}")
        return []
