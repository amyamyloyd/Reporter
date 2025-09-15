# Function Library Documentation - Excel Reporting POC

## Overview
Complete catalog of internal functions and methods for direct system integration with LangChain agents. This documentation provides detailed function signatures, parameter descriptions, and integration patterns for AI agent orchestration.

**Purpose**: Enable LangChain agents to directly call internal functions without going through REST endpoints  
**Integration**: Functions can be wrapped as LangChain tools for agent execution  
**Error Handling**: Comprehensive error patterns and exception types documented

---

## Core File Processing Functions

### `extract_file_metadata_from_saved_file(file_path: str) -> Dict[str, Any]`
**Purpose**: Extract metadata from saved Excel files for analysis  
**Module**: `excel_processor.py`  
**Business Context**: Core function for file analysis workflow

**Parameters**:
- `file_path` (str): Path to the saved Excel file
  - **Validation**: Must be valid file path to .xlsx or .xls file
  - **Format**: Absolute or relative path string
  - **Example**: `"/path/to/sales_data.xlsx"`

**Returns**:
- `Dict[str, Any]`: File metadata structure
  - `sheets`: Dictionary of sheet metadata
  - `fields`: Original field names from Excel
  - `normalized_fields`: DuckDB-compatible field names
  - `field_mapping`: Original to normalized field mapping
  - `types`: Data types for each field
  - `row_count`: Number of rows per sheet

**Side Effects**:
- Reads Excel file from disk
- No database modifications
- No file system changes

**Error Handling**:
- `FileNotFoundError`: If file path doesn't exist
- `ValueError`: If file is not a valid Excel format
- `Exception`: Generic error with error message in return dict

**Performance Characteristics**:
- Execution time: 0.1-2.0 seconds depending on file size
- Memory usage: Scales with file size (typically 2-5x file size)
- Handles files up to 50MB efficiently

**LangChain Integration Example**:
```python
from langchain.tools import tool
from excel_processor import extract_file_metadata_from_saved_file

@tool
def analyze_excel_file(file_path: str) -> dict:
    """
    Analyze Excel file and extract metadata for agent processing.
    
    Args:
        file_path: Path to the Excel file to analyze
        
    Returns:
        Dict containing file metadata and field information
    """
    try:
        metadata = extract_file_metadata_from_saved_file(file_path)
        if "error" in metadata:
            return {"success": False, "error": metadata["error"]}
        return {"success": True, "metadata": metadata}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

### `validate_excel_files(files: List[UploadFile]) -> Dict[str, Any]`
**Purpose**: Validate uploaded Excel files before processing  
**Module**: `excel_processor.py`  
**Business Context**: File upload validation and security check

**Parameters**:
- `files` (List[UploadFile]): List of uploaded file objects
  - **Validation**: Must be FastAPI UploadFile objects
  - **Constraints**: Maximum 5 files, 50MB per file
  - **Formats**: Only .xlsx and .xls files accepted

**Returns**:
- `Dict[str, Any]`: Validation results
  - `valid_files`: List of valid file objects
  - `errors`: List of validation error messages
  - `file_count`: Number of files processed

**Side Effects**:
- Validates file headers and formats
- No file system modifications
- No database operations

**Error Handling**:
- `ValueError`: For invalid file formats or sizes
- `TypeError`: For non-UploadFile objects
- Returns error messages in validation results

**Performance Characteristics**:
- Execution time: 0.01-0.1 seconds per file
- Memory usage: Minimal (header validation only)
- Validates up to 5 files simultaneously

**LangChain Integration Example**:
```python
@tool
def validate_uploaded_files(files: List[UploadFile]) -> dict:
    """
    Validate uploaded Excel files for processing.
    
    Args:
        files: List of FastAPI UploadFile objects
        
    Returns:
        Dict with validation results and valid files
    """
    return validate_excel_files(files)
```

---

### `_normalize_column_name(name: str) -> str`
**Purpose**: Normalize Excel column names for DuckDB compatibility  
**Module**: `excel_processor.py`  
**Business Context**: Data preparation for database operations

**Parameters**:
- `name` (str): Original column name from Excel
  - **Validation**: Non-empty string
  - **Constraints**: Will be sanitized for SQL safety
  - **Example**: `"Company Code"` → `"Company_Code"`

**Returns**:
- `str`: Normalized column name safe for SQL
  - Removes special characters
  - Ensures starts with letter/underscore
  - Limits length to 64 characters
  - Handles empty names

**Side Effects**:
- Pure function - no side effects
- No file system or database operations

**Error Handling**:
- Handles empty strings gracefully
- Converts non-string inputs to string
- No exceptions raised

**Performance Characteristics**:
- Execution time: <0.001 seconds
- Memory usage: Minimal
- Processes any string length efficiently

---

## Database Management Functions

### `create_persistent_database() -> duckdb.DuckDBPyConnection`
**Purpose**: Create persistent DuckDB connection for data storage  
**Module**: `duckdb_manager.py`  
**Business Context**: Database connection management for session persistence

**Parameters**: None

**Returns**:
- `duckdb.DuckDBPyConnection`: Active database connection
  - **Lifetime**: Must be closed after use
  - **Database**: `excel_reporting.db` file
  - **Persistence**: Data survives application restarts

**Side Effects**:
- Creates database file if it doesn't exist
- Establishes database connection
- No data modifications

**Error Handling**:
- `Exception`: Database connection failures
- `OSError`: File system permission issues
- Raises exception on failure

**Performance Characteristics**:
- Execution time: 0.1-0.5 seconds
- Memory usage: ~10MB for connection
- Connection can be reused for multiple operations

**Transaction Boundaries**:
- No automatic transaction management
- Manual commit/rollback required
- Connection must be explicitly closed

**LangChain Integration Example**:
```python
@tool
def get_database_connection() -> dict:
    """
    Create persistent DuckDB database connection.
    
    Returns:
        Dict with connection status and connection object
    """
    try:
        conn = create_persistent_database()
        return {"success": True, "connection": conn}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

### `create_document_registry_table(conn: duckdb.DuckDBPyConnection) -> bool`
**Purpose**: Create document registry table for classification  
**Module**: `duckdb_manager.py`  
**Business Context**: Database schema initialization

**Parameters**:
- `conn` (duckdb.DuckDBPyConnection): Active database connection
  - **Validation**: Must be valid DuckDB connection
  - **State**: Connection must be open

**Returns**:
- `bool`: True if table created successfully, False otherwise

**Side Effects**:
- Creates `doc_registry` table if it doesn't exist
- No data modifications
- Safe to call multiple times

**Error Handling**:
- `Exception`: Database operation failures
- Returns False on error
- Logs error messages

**Performance Characteristics**:
- Execution time: 0.1-0.3 seconds
- Memory usage: Minimal
- Idempotent operation

**Database Schema Created**:
```sql
CREATE TABLE doc_registry (
    id INTEGER PRIMARY KEY,
    document_type VARCHAR NOT NULL,
    document_type_code VARCHAR NOT NULL,
    field_pattern VARCHAR NOT NULL,
    reuse_regularly BOOLEAN DEFAULT false,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description VARCHAR,
    example_filename VARCHAR,
    latest_version VARCHAR DEFAULT '1.0'
)
```

---

### `check_document_type_by_fields(conn: duckdb.DuckDBPyConnection, fields: List[str]) -> Optional[dict]`
**Purpose**: Check if document type exists in registry based on field names  
**Module**: `duckdb_manager.py`  
**Business Context**: Document classification and type detection

**Parameters**:
- `conn` (duckdb.DuckDBPyConnection): Active database connection
- `fields` (List[str]): List of field names from Excel file
  - **Validation**: Non-empty list of strings
  - **Format**: Field names as they appear in Excel

**Returns**:
- `Optional[dict]`: Document type information if found, None otherwise
  - `document_type`: Human-readable document type
  - `document_code`: Short code for the type
  - `field_pattern`: Pattern used for matching
  - `confidence`: Match confidence score

**Side Effects**:
- Reads from database
- No data modifications
- No file system operations

**Error Handling**:
- `Exception`: Database query failures
- Returns None on error
- Logs error messages

**Performance Characteristics**:
- Execution time: 0.05-0.2 seconds
- Memory usage: Minimal
- Scales with registry size

**LangChain Integration Example**:
```python
@tool
def classify_document_type(conn: duckdb.DuckDBPyConnection, fields: List[str]) -> dict:
    """
    Classify document type based on field names.
    
    Args:
        conn: Active DuckDB connection
        fields: List of field names from Excel file
        
    Returns:
        Dict with classification results
    """
    try:
        result = check_document_type_by_fields(conn, fields)
        if result:
            return {"success": True, "classification": result}
        else:
            return {"success": False, "message": "No matching document type found"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

## Agent System Functions

### `create_file_analyzer() -> AssistantAgent`
**Purpose**: Create AutoGen agent for Excel file analysis  
**Module**: `agents/file_analyzer.py`  
**Business Context**: AI agent creation for file processing workflow

**Parameters**: None

**Returns**:
- `AssistantAgent`: Configured AutoGen agent
  - **Model**: GPT-4o for analysis
  - **Capabilities**: Field extraction and pattern recognition
  - **Output**: Structured JSON responses

**Side Effects**:
- Creates agent instance
- No database or file operations
- Agent ready for conversation

**Error Handling**:
- `ImportError`: AutoGen import failures
- `Exception`: Agent configuration errors
- Raises exception on failure

**Performance Characteristics**:
- Creation time: 0.1-0.5 seconds
- Memory usage: ~50MB per agent
- Agent can be reused for multiple conversations

**Agent Configuration**:
- **Model**: GPT-4o with 120-second timeout
- **System Message**: Field extraction focused
- **Output Format**: JSON with field information
- **Human Input**: Never (automated for POC)

**LangChain Integration Example**:
```python
@tool
def create_analysis_agent() -> dict:
    """
    Create AutoGen file analysis agent.
    
    Returns:
        Dict with agent creation status
    """
    try:
        agent = create_file_analyzer()
        return {"success": True, "agent": agent}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

### `analyze_single_file(file_metadata: Dict[str, Any], user_input: str) -> Dict[str, Any]`
**Purpose**: Analyze single Excel file using AutoGen agents  
**Module**: `agents/file_analyzer.py`  
**Business Context**: Core file analysis workflow execution

**Parameters**:
- `file_metadata` (Dict[str, Any]): File metadata from extraction
  - **Required Keys**: `sheets`, `fields`, `types`
  - **Format**: Output from `extract_file_metadata_from_saved_file`
- `user_input` (str): User's description of file purpose
  - **Validation**: Non-empty string
  - **Length**: 3-1000 characters
  - **Example**: `"This file contains monthly sales data"`

**Returns**:
- `Dict[str, Any]`: Analysis results
  - `success`: Boolean indicating success
  - `analysis`: Structured analysis data
  - `conversation_summary`: Agent conversation summary
  - `error`: Error message if failed

**Side Effects**:
- Creates agent conversation
- Updates agent memory
- No database modifications
- No file system changes

**Error Handling**:
- `ValueError`: Invalid input parameters
- `Exception`: Agent conversation failures
- Returns error in response dict

**Performance Characteristics**:
- Execution time: 2-10 seconds (LLM dependent)
- Memory usage: ~100MB during analysis
- Scales with file complexity

**Transaction Boundaries**:
- Single operation
- No rollback needed
- Stateless operation

**LangChain Integration Example**:
```python
@tool
def analyze_excel_file_with_agent(file_metadata: dict, user_input: str) -> dict:
    """
    Analyze Excel file using AutoGen agents.
    
    Args:
        file_metadata: File metadata from extraction
        user_input: User's description of file purpose
        
    Returns:
        Dict with analysis results
    """
    return analyze_single_file(file_metadata, user_input)
```

---

## Utility Functions

### `save_metadata(doc_id: str, metadata: Dict[str, Any]) -> bool`
**Purpose**: Save document metadata to JSON file  
**Module**: `utils/json_store.py`  
**Business Context**: Document metadata persistence

**Parameters**:
- `doc_id` (str): Document identifier
  - **Format**: `{filename}_{document_type_code}_{timestamp}`
  - **Example**: `"hospital_ledger_fy2024_001"`
- `metadata` (Dict[str, Any]): Document metadata to save
  - **Required Keys**: `filename`, `fields`, `record_count`
  - **Format**: Structured metadata dictionary

**Returns**:
- `bool`: True if save successful, False otherwise

**Side Effects**:
- Creates/updates JSON file in `stored_queries/` directory
- No database operations
- File system write operation

**Error Handling**:
- `OSError`: File system permission issues
- `TypeError`: Invalid metadata format
- Returns False on error

**Performance Characteristics**:
- Execution time: 0.01-0.1 seconds
- Memory usage: Minimal
- File size: Typically 1-10KB

**File Format**:
```json
{
  "doc_id": "hospital_ledger_fy2024_001",
  "filename": "hospital_ledger.xlsx",
  "fields": ["Vendor", "Date", "Amount"],
  "record_count": 1220,
  "created_at": "2024-01-01T12:00:00Z"
}
```

---

### `load_metadata(doc_id: str) -> Optional[Dict[str, Any]]`
**Purpose**: Load document metadata from JSON file  
**Module**: `utils/json_store.py`  
**Business Context**: Document metadata retrieval

**Parameters**:
- `doc_id` (str): Document identifier
  - **Format**: Must match saved document ID
  - **Validation**: Non-empty string

**Returns**:
- `Optional[Dict[str, Any]]`: Metadata if found, None otherwise

**Side Effects**:
- Reads JSON file from disk
- No modifications
- No database operations

**Error Handling**:
- `FileNotFoundError`: If file doesn't exist
- `JSONDecodeError`: If file is corrupted
- Returns None on error

**Performance Characteristics**:
- Execution time: 0.01-0.05 seconds
- Memory usage: Minimal
- Handles files up to 1MB efficiently

---

### `append_query_to_metadata(doc_id: str, query_data: Dict[str, Any]) -> bool`
**Purpose**: Add query to document metadata  
**Module**: `utils/json_store.py`  
**Business Context**: Query persistence and document association

**Parameters**:
- `doc_id` (str): Document identifier
- `query_data` (Dict[str, Any]): Query information
  - **Required Keys**: `query_name`, `query_text`, `sql`
  - **Format**: Query metadata dictionary

**Returns**:
- `bool`: True if append successful, False otherwise

**Side Effects**:
- Updates existing JSON file
- Adds query to queries array
- No database operations

**Error Handling**:
- `FileNotFoundError`: If document file doesn't exist
- `JSONDecodeError`: If file is corrupted
- Returns False on error

**Performance Characteristics**:
- Execution time: 0.01-0.1 seconds
- Memory usage: Minimal
- File grows with each query

---

### `append_report_to_metadata(doc_id: str, report_data: Dict[str, Any]) -> bool`
**Purpose**: Add report to document metadata  
**Module**: `utils/json_store.py`  
**Business Context**: Report persistence and document association

**Parameters**:
- `doc_id` (str): Document identifier
- `report_data` (Dict[str, Any]): Report information
  - **Required Keys**: `report_name`, `report_config`
  - **Format**: Report metadata dictionary

**Returns**:
- `bool`: True if append successful, False otherwise

**Side Effects**:
- Updates existing JSON file
- Adds report to reports array
- No database operations

**Error Handling**:
- `FileNotFoundError`: If document file doesn't exist
- `JSONDecodeError`: If file is corrupted
- Returns False on error

**Performance Characteristics**:
- Execution time: 0.01-0.1 seconds
- Memory usage: Minimal
- File grows with each report

---

## Query and Report Functions

### `save_query(conn: duckdb.DuckDBPyConnection, query_data: Dict[str, Any]) -> bool`
**Purpose**: Save query to DuckDB database  
**Module**: `utils/duckdb_manager.py`  
**Business Context**: Query persistence for reuse and navigation

**Parameters**:
- `conn` (duckdb.DuckDBPyConnection): Active database connection
- `query_data` (Dict[str, Any]): Query information
  - **Required Keys**: `doc_id`, `query_name`, `query_text`, `sql`
  - **Optional Keys**: `description`, `is_favorite`

**Returns**:
- `bool`: True if save successful, False otherwise

**Side Effects**:
- Inserts record into `saved_queries` table
- No file system operations
- Database write operation

**Error Handling**:
- `Exception`: Database operation failures
- `ValueError`: Invalid query data
- Returns False on error

**Performance Characteristics**:
- Execution time: 0.05-0.2 seconds
- Memory usage: Minimal
- Scales with database size

**Database Schema**:
```sql
CREATE TABLE saved_queries (
    id INTEGER PRIMARY KEY,
    doc_id VARCHAR NOT NULL,
    query_name VARCHAR NOT NULL,
    query_text VARCHAR NOT NULL,
    sql VARCHAR NOT NULL,
    description VARCHAR,
    is_favorite BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

### `save_report(conn: duckdb.DuckDBPyConnection, report_data: Dict[str, Any]) -> bool`
**Purpose**: Save report to DuckDB database  
**Module**: `utils/duckdb_manager.py`  
**Business Context**: Report persistence for reuse and navigation

**Parameters**:
- `conn` (duckdb.DuckDBPyConnection): Active database connection
- `report_data` (Dict[str, Any]): Report information
  - **Required Keys**: `doc_id`, `report_name`, `report_config`
  - **Optional Keys**: `description`, `is_favorite`

**Returns**:
- `bool`: True if save successful, False otherwise

**Side Effects**:
- Inserts record into `saved_reports` table
- No file system operations
- Database write operation

**Error Handling**:
- `Exception`: Database operation failures
- `ValueError`: Invalid report data
- Returns False on error

**Performance Characteristics**:
- Execution time: 0.05-0.2 seconds
- Memory usage: Minimal
- Scales with database size

---

### `ensure_all_tables_exist(conn: duckdb.DuckDBPyConnection) -> bool`
**Purpose**: Ensure all required database tables exist  
**Module**: `utils/duckdb_manager.py`  
**Business Context**: Database schema initialization and maintenance

**Parameters**:
- `conn` (duckdb.DuckDBPyConnection): Active database connection

**Returns**:
- `bool`: True if all tables exist or created successfully

**Side Effects**:
- Creates missing tables
- No data modifications
- Safe to call multiple times

**Error Handling**:
- `Exception`: Database operation failures
- Returns False on error
- Logs error messages

**Performance Characteristics**:
- Execution time: 0.1-0.5 seconds
- Memory usage: Minimal
- Idempotent operation

**Tables Created**:
- `doc_registry`: Document type registry
- `saved_queries`: Saved query storage
- `saved_reports`: Saved report storage
- `uploaded_files`: File metadata storage

---

## Error Handling Patterns

### Standard Error Response Format
All functions follow consistent error handling patterns:

```python
# Success Response
{
    "success": True,
    "data": {...},
    "message": "Operation completed successfully"
}

# Error Response
{
    "success": False,
    "error": "Error message describing what went wrong",
    "error_type": "ValueError",
    "details": {...}
}
```

### Exception Types
- **`ValueError`**: Invalid input parameters
- **`TypeError`**: Wrong parameter types
- **`FileNotFoundError`**: Missing files
- **`OSError`**: File system permission issues
- **`JSONDecodeError`**: Corrupted JSON files
- **`Exception`**: Generic errors

### Error Recovery Strategies
1. **Validation Errors**: Return error response, don't modify state
2. **File Errors**: Log error, return safe fallback
3. **Database Errors**: Rollback transaction, return error
4. **Network Errors**: Retry with exponential backoff

---

## Performance Optimization Guidelines

### Memory Management
- **File Processing**: Process files in chunks for large datasets
- **Database Connections**: Use connection pooling for multiple operations
- **Agent Creation**: Reuse agents when possible
- **JSON Storage**: Stream large JSON files

### Execution Time Optimization
- **Database Queries**: Use prepared statements for repeated queries
- **File I/O**: Use async operations where possible
- **Agent Conversations**: Limit conversation length
- **Validation**: Early validation to fail fast

### Resource Cleanup
- **Database Connections**: Always close connections
- **File Handles**: Use context managers
- **Agent Memory**: Clear conversation history
- **Temporary Files**: Clean up after processing

---

## LangChain Integration Patterns

### Tool Wrapping Strategy
```python
from langchain.tools import tool
from typing import Dict, Any

def create_langchain_tool(func, name: str, description: str):
    """Create LangChain tool from internal function"""
    
    @tool(name=name, description=description)
    def wrapped_function(*args, **kwargs) -> str:
        try:
            result = func(*args, **kwargs)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            }, indent=2)
    
    return wrapped_function

# Example usage
analyze_file_tool = create_langchain_tool(
    extract_file_metadata_from_saved_file,
    "analyze_excel_file",
    "Extract metadata from Excel file for analysis"
)
```

### Agent Integration Examples
```python
from langchain.agents import create_react_agent
from langchain.llms import OpenAI

# Create agent with function tools
tools = [
    create_langchain_tool(extract_file_metadata_from_saved_file, "analyze_file", "Analyze Excel file"),
    create_langchain_tool(analyze_single_file, "analyze_with_agent", "Analyze file with AI agent"),
    create_langchain_tool(save_query, "save_query", "Save query to database")
]

agent = create_react_agent(
    llm=OpenAI(temperature=0),
    tools=tools,
    prompt=prompt
)
```

### Error Handling in LangChain
```python
def safe_function_call(func, *args, **kwargs):
    """Safely call function with error handling for LangChain"""
    try:
        result = func(*args, **kwargs)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Function {func.__name__} failed: {e}")
        return {"success": False, "error": str(e)}
```

This comprehensive function library documentation enables LangChain agents to directly integrate with the Excel Reporting POC system, providing detailed function signatures, error handling patterns, and integration examples for seamless AI agent orchestration.
