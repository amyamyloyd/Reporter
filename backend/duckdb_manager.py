# DuckDB database operations for Phase 1
# ONLY handle DuckDB database operations

import duckdb
import pandas as pd
from typing import Optional, List, Dict, Any
import re
import os

def create_persistent_database() -> duckdb.DuckDBPyConnection:
    """
    Create persistent DuckDB connection for data persistence
    
    Creates a persistent DuckDB connection using 'excel_reporting.db' file
    to maintain data between user sessions. This replaces the previous
    in-memory approach for better data persistence.
    
    Returns:
        DuckDB connection object
        
    Example:
        conn = create_persistent_database()
        # Use connection for persistent data storage
        conn.close()  # Always close when done
    """
    try:
        # Create persistent DuckDB connection using excel_reporting.db
        # This ensures data persists between user sessions
        # Production database name: excel_reporting.db
        import os
        # Get the absolute path to the backend directory
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(backend_dir, 'excel_reporting.db')
        conn = duckdb.connect(db_path)
        
        # Note: DuckDB doesn't support SQLite PRAGMA commands
        # Foreign key constraints are handled differently in DuckDB
        
        print("Created persistent DuckDB database: excel_reporting.db")
        return conn
        
    except Exception as e:
        print(f"Failed to create DuckDB database: {e}")
        raise

def create_document_registry_table(conn: duckdb.DuckDBPyConnection) -> bool:
    """
    Create the document registry table structure
    
    This table stores document types and their field patterns for auto-classification.
    Run this function once to set up the registry structure.
    
    Args:
        conn: DuckDB connection
        
    Returns:
        bool: True if table created successfully
        
    Example:
        success = create_document_registry_table(conn)
        if success:
            print("Registry table created successfully")
    """
    try:
        # Create the doc_registry table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS doc_registry (
                id INTEGER PRIMARY KEY,
                document_type VARCHAR NOT NULL,
                document_type_code VARCHAR NOT NULL,
                field_pattern VARCHAR NOT NULL,
                reuse_regularly BOOLEAN DEFAULT false,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description VARCHAR,
                example_filename VARCHAR
            )
        """)
        
        print(f"Created document registry table structure")
        return True
        
    except Exception as e:
        print(f"Error creating document registry table: {e}")
        return False

def check_document_type_by_fields(conn: duckdb.DuckDBPyConnection, fields: List[str]) -> Optional[dict]:
    """
    Check if a document type exists in the registry based on field names.
    
    This function is used to determine if a new document type discovered
    in an Excel file matches an existing one in the registry.
    
    Args:
        conn: DuckDB connection
        fields: List of field names from the Excel file
        
    Returns:
        dict: Document type information if found, None otherwise
        
    Example:
        doc_info = check_document_type_by_fields(
            conn, ["Invoice_Number", "Date", "Amount"]
        )
        if doc_info:
            print(f"Found document type: {doc_info['document_type']}")
        else:
            print("No matching document type found.")
    """
    try:
        # Convert fields list to sorted string for consistent comparison
        fields_str = "|".join(sorted(fields))
        
        # Query the registry for a matching document type
        result = conn.execute("""
            SELECT id, document_type, document_type_code, field_pattern, reuse_regularly, description
            FROM doc_registry
            WHERE field_pattern = ?
        """, [fields_str])
        
        match = result.fetchone()
        
        if match:
            return {
                "id": match[0],
                "document_type": match[1],
                "document_type_code": match[2],
                "field_pattern": match[3],
                "reuse_regularly": match[4],
                "description": match[5]
            }
        # No match found
        return None
        
    except Exception as e:
        print(f"Error checking document type by fields: {e}")
        return None

def add_new_document_type(conn: duckdb.DuckDBPyConnection, document_type: str, 
                          document_type_code: str, fields: List[str], 
                          reuse_regularly: bool, description: str = "") -> bool:
    """
    Add a new document type to the registry
    
    This function adds newly discovered document types to the registry
    so they can be automatically recognized in future uploads.
    
    Args:
        conn: DuckDB connection
        document_type: Human-readable document type name
        document_type_code: Short code for the document type
        fields: List of field names for pattern matching
        reuse_regularly: Whether this document type is used regularly
        description: Optional description of the document type
        
    Returns:
        bool: True if successfully added to registry
        
    Example:
        success = add_new_document_type(
            conn, "Purchase Orders", "PO", ["PO_Number", "Vendor", "Amount"], 
            True, "Purchase order data for procurement"
        )
    """
    try:
        # Convert fields list to sorted string for consistent storage
        fields_str = "|".join(sorted(fields))
        
        # Check if document type already exists
        existing = conn.execute("""
            SELECT id FROM doc_registry WHERE document_type_code = ?
        """, [document_type_code]).fetchone()
        
        if existing:
            # Update existing record
            conn.execute("""
                UPDATE doc_registry 
                SET field_pattern = ?, reuse_regularly = ?, description = ?, updated_date = CURRENT_TIMESTAMP
                WHERE document_type_code = ?
            """, [fields_str, reuse_regularly, description, document_type_code])
            print(f"Updated existing document type: {document_type}")
        else:
            # Get next available ID
            next_id_result = conn.execute("""
                SELECT COALESCE(MAX(id), 0) + 1 FROM doc_registry
            """).fetchone()
            next_id = next_id_result[0] if next_id_result else 1
            
            # Insert new record with explicit ID
            conn.execute("""
                INSERT INTO doc_registry (id, document_type, document_type_code, field_pattern, reuse_regularly, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [next_id, document_type, document_type_code, fields_str, reuse_regularly, description])
            print(f"Added new document type to registry: {document_type}")
        
        return True
        
    except Exception as e:
        print(f"Error adding document type to registry: {e}")
        return False

def get_document_registry(conn: duckdb.DuckDBPyConnection) -> List[Dict[str, Any]]:
    """
    Retrieve all document types from the registry
    
    Args:
        conn: DuckDB connection
        
    Returns:
        List of dictionaries containing document type information
        
    Example:
        registry = get_document_registry(conn)
        for doc in registry:
            print(f"{doc['document_type']}: {doc['document_type_code']}")
    """
    try:
        result = conn.execute("""
            SELECT id, document_type, document_type_code, field_pattern, 
                   reuse_regularly, description, created_date, updated_date
            FROM doc_registry
            ORDER BY document_type
        """).fetchall()
        
        registry = []
        for row in result:
            registry.append({
                "id": row[0],
                "document_type": row[1],
                "document_type_code": row[2],
                "field_pattern": row[3],
                "reuse_regularly": row[4],
                "description": row[5],
                "created_date": row[6],
                "updated_date": row[7]
            })
        
        return registry
        
    except Exception as e:
        print(f"Error retrieving document registry: {e}")
        return []

def extract_data_version_from_filename(filename: str) -> str:
    """
    Extract data version from filename timestamp
    
    Extracts the date portion from filenames like:
    'company_financials_2025-08-27_160349.xlsx' -> '2025-08-27'
    
    Args:
        filename (str): Filename with timestamp format
        
    Returns:
        str: Extracted date in YYYY-MM-DD format, or 'unknown' if not found
        
    Example:
        version = extract_data_version_from_filename('inventory_2025-08-27_143022.xlsx')
        # Returns: '2025-08-27'
    """
    try:
        # Look for date pattern in filename: YYYY-MM-DD
        # This matches the timestamp format used in the upload endpoint
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(date_pattern, filename)
        
        if match:
            data_version = match.group(1)
            print(f"Extracted data version '{data_version}' from filename: {filename}")
            return data_version
        else:
            print(f"No date pattern found in filename: {filename}")
            return "unknown"
            
    except Exception as e:
        print(f"Error extracting data version from filename {filename}: {e}")
        return "unknown"

def dataframe_to_table(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame, table_name: str) -> bool:
    """
    Convert pandas DataFrame to DuckDB table using df.to_sql()
    
    Updated to work with persistent connections and provide better error handling.
    Column names are expected to be pre-normalized during upload.
    
    Args:
        conn: DuckDB connection (now persistent)
        df: DataFrame to convert (with normalized column names)
        table_name: Name for the DuckDB table
        
    Returns:
        bool: Success status
        
    Example:
        success = dataframe_to_table(conn, inventory_df, "inventory_data_2025_08_27")
        if success:
            print("Table created successfully in persistent database")
    """
    try:
        print(f"DEBUG: Starting table creation for '{table_name}'")
        print(f"DEBUG: DataFrame shape: {df.shape}")
        print(f"DEBUG: DataFrame columns: {list(df.columns)}")
        print(f"DEBUG: Connection type: {type(conn)}")
        
        # Validate table name (DuckDB safe)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            print(f"Invalid table name: {table_name}")
            return False
            
        # Check if DataFrame is empty
        if df.empty:
            print(f"DataFrame is empty for table {table_name}")
            return False
            
        # Sanitize column names to avoid spaces/special characters
        # This ensures DuckDB compatibility even if normalization failed
        df.columns = [re.sub(r'[^a-zA-Z0-9_]', '_', col).strip('_') for col in df.columns]
        print(f"DEBUG: Sanitized columns: {list(df.columns)}")
        
        # Convert DataFrame to DuckDB table using DuckDB's native DataFrame support
        # DuckDB can directly create tables from pandas DataFrames
        
        # First, drop table if it exists
        print(f"DEBUG: Dropping table if exists: {table_name}")
        conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        print(f"DEBUG: Table dropped successfully")
        
        # Register the DataFrame as a virtual table in DuckDB
        print(f"DEBUG: Registering DataFrame as 'df_temp'")
        conn.register('df_temp', df)
        print(f"DEBUG: DataFrame registered successfully")
        
        # Create table from the registered DataFrame
        print(f"DEBUG: Creating table: {table_name}")
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_temp")
        print(f"DEBUG: Table created successfully")
        
        # Unregister the temporary view to clean up
        print(f"DEBUG: Unregistering temporary view")
        conn.unregister('df_temp')
        print(f"DEBUG: Temporary view unregistered")
        
        # Verify table was created and data loaded correctly
        result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = result.fetchone()[0]
        
        if row_count == len(df):
            print(f"Successfully created persistent table '{table_name}' with {row_count} rows")
            return True
        else:
            print(f"Table created but row count mismatch: expected {len(df)}, got {row_count}")
            return False
            
    except Exception as e:
        print(f"ERROR creating table {table_name}: {e}")
        print(f"ERROR type: {type(e).__name__}")
        print(f"ERROR details: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def _sanitize_column_name(name: str) -> str:
    """
    Sanitize column names for DuckDB compatibility
    
    Excel column names can contain spaces, special characters, and
    other elements that cause SQL issues. This function creates
    safe column names while maintaining readability.
    
    Args:
        name (str): Original column name from Excel
        
    Returns:
        str: Sanitized column name safe for SQL
        
    Example:
        safe_name = _sanitize_column_name("Company Code")  # Returns: "Company_Code"
        safe_name = _sanitize_column_name("Cost ($)")     # Returns: "Cost___"
    """
    # Replace spaces and special chars with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    
    # Ensure starts with letter or underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = 'col_' + sanitized
        
    # Handle empty names
    if not sanitized:
        sanitized = 'unnamed_column'
        
    # Limit length and remove double underscores
    sanitized = re.sub(r'_+', '_', sanitized)[:64]
    
    return sanitized.strip('_')

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
        # Query system tables to get all user tables
        result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'")
        tables = [row[0] for row in result.fetchall()]
        return tables
    except Exception as e:
        print(f"Error listing tables: {e}")
        return []

def verify_table_data(conn: duckdb.DuckDBPyConnection, table_name: str, expected_rows: int) -> bool:
    """
    Verify that a table contains the expected amount of data
    
    This function helps validate that Excel data was properly loaded into DuckDB.
    
    Args:
        conn: DuckDB connection
        table_name: Name of the table to verify
        expected_rows: Expected number of rows from Excel file
        
    Returns:
        bool: True if row count matches, False otherwise
        
    Example:
        is_valid = verify_table_data(conn, "inventory_2025_08_27", 150)
        if is_valid:
            print("Data verification passed")
    """
    try:
        # Count rows in the table
        result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        actual_rows = result.fetchone()[0]
        
        # Compare with expected count
        if actual_rows == expected_rows:
            print(f"Data verification passed: {actual_rows} rows in table '{table_name}'")
            return True
        else:
            print(f"Data verification failed: expected {expected_rows}, got {actual_rows} rows")
            return False
            
    except Exception as e:
        print(f"Error verifying table data for {table_name}: {e}")
        return False
