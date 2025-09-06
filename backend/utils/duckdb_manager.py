"""
Extended DuckDB Manager for AutoGen Excel Intelligence System

This module extends the existing duckdb_manager.py with additional functions
required for the new endpoints: saved_queries, saved_reports tables.

Key Functions:
- create_query_table() - Create saved_queries table
- create_report_table() - Create saved_reports table  
- save_query() - Save query to DuckDB and return success status
- save_report() - Save report to DuckDB and return success status
- get_saved_queries() - Retrieve saved queries with filtering
- get_saved_reports() - Retrieve saved reports with filtering
"""

import duckdb
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import hashlib
import re

# Import the base duckdb_manager functions
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from duckdb_manager import create_persistent_database

# Configure logging for DuckDB operations
logger = logging.getLogger(__name__)

def create_query_table(conn: duckdb.DuckDBPyConnection) -> bool:
    """
    Create the saved_queries table structure
    
    This table stores all saved queries with their metadata for retrieval
    and reuse. Stores full SQL and query parameters (NOT normalized).
    
    Args:
        conn: DuckDB connection
        
    Returns:
        bool: True if table created successfully
        
    Example:
        success = create_query_table(conn)
        if success:
            print("saved_queries table created successfully")
    """
    try:
        # Create the saved_queries table with all required fields
        # Updated schema includes intelligent classification fields for query reuse
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_queries (
                id INTEGER PRIMARY KEY,
                doc_id VARCHAR NOT NULL,
                document_type VARCHAR,  -- Document type (e.g., "Employee Data")
                document_type_code VARCHAR,  -- Document type code (e.g., "EMP")
                query_name VARCHAR NOT NULL,
                query_text TEXT NOT NULL,
                sql TEXT NOT NULL,
                sql_hash VARCHAR,  -- Hash of normalized SQL for uniqueness detection
                is_global BOOLEAN DEFAULT FALSE,  -- True if saved globally, False if doc-specific only
                tags TEXT,  -- JSON array of tags
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                use_count INTEGER DEFAULT 0,
                description TEXT
            )
        """)
        
        logger.info("Created saved_queries table structure")
        return True
        
    except Exception as e:
        logger.error(f"Error creating saved_queries table: {e}")
        return False

def create_report_table(conn: duckdb.DuckDBPyConnection) -> bool:
    """
    Create the saved_reports table structure
    
    This table stores all saved reports with their configuration and metadata
    for retrieval and reuse. Stores full report parameters (NOT normalized).
    
    Args:
        conn: DuckDB connection
        
    Returns:
        bool: True if table created successfully
        
    Example:
        success = create_report_table(conn)
        if success:
            print("saved_reports table created successfully")
    """
    try:
        # Create the saved_reports table with all required fields
        # Updated schema includes intelligent classification fields for report reuse
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_reports (
                id INTEGER PRIMARY KEY,
                doc_id VARCHAR NOT NULL,
                document_type VARCHAR,  -- Document type (e.g., "Employee Data")
                document_type_code VARCHAR,  -- Document type code (e.g., "EMP")
                report_name VARCHAR NOT NULL,
                sql TEXT,  -- SQL used to generate report
                sql_hash VARCHAR,  -- Hash of normalized SQL for uniqueness detection
                is_global BOOLEAN DEFAULT FALSE,  -- True if saved globally, False if doc-specific only
                filters TEXT,  -- JSON object of filters
                group_by TEXT,  -- JSON array of group by fields
                format VARCHAR,  -- table, chart, etc.
                chart VARCHAR,  -- bar, line, pie, etc.
                output_type VARCHAR,  -- html, xlsx, json
                description TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_generated TIMESTAMP,
                generation_count INTEGER DEFAULT 0
            )
        """)
        
        logger.info("Created saved_reports table structure")
        return True
        
    except Exception as e:
        logger.error(f"Error creating saved_reports table: {e}")
        return False

def save_query(conn: duckdb.DuckDBPyConnection, doc_id: str, 
               document_type: str, document_type_code: str,
               query_name: str, query_text: str, sql: str, 
               sql_hash: str, is_global: bool,
               tags: List[str] = None, description: str = "") -> bool:
    """
    Save a query to the saved_queries table with intelligent classification
    
    Stores query information in DuckDB with document type awareness and global/local
    classification. This enables intelligent query reuse across similar document types
    and prevents duplicate queries with different names.
    
    Args:
        conn: DuckDB connection for database operations
        doc_id: Document identifier for the source document
        document_type: Document type name (e.g., "Employee Data")
        document_type_code: Document type code (e.g., "EMP")
        query_name: Name of the query (generated by LLM or fallback)
        query_text: Original natural language query text
        sql: Generated SQL query
        sql_hash: MD5 hash of normalized SQL for uniqueness detection
        is_global: True if saved globally for reuse, False if doc-specific only
        tags: List of tags for categorization (optional)
        description: Optional description of the query
        
    Returns:
        bool: True if save successful, False otherwise
        
    Example:
        success = save_query(
            conn, "hospital_ledger_fy2024_001", "Financial Data", "FIN",
            "Quarterly Vendor Spend", "How much did we spend on Vendor X in Q2?",
            "SELECT SUM(Amount) FROM hospital_ledger_fy2024_001 WHERE Vendor = 'Vendor X'",
            "abc123hash", True, ["vendor", "q2", "spending"]
        )
    """
    try:
        # Ensure saved_queries table exists
        create_query_table(conn)
        
        # Convert tags list to JSON string
        tags_json = json.dumps(tags) if tags else "[]"
        
        # Get next available ID
        next_id_result = conn.execute("""
            SELECT COALESCE(MAX(id), 0) + 1 FROM saved_queries
        """).fetchone()
        next_id = next_id_result[0] if next_id_result else 1
        
        # Insert query record with intelligent classification fields
        conn.execute("""
            INSERT INTO saved_queries (id, doc_id, document_type, document_type_code, 
                                     query_name, query_text, sql, sql_hash, is_global, 
                                     tags, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [next_id, doc_id, document_type, document_type_code, query_name, 
              query_text, sql, sql_hash, is_global, tags_json, description])
        
        logger.info(f"Successfully saved query '{query_name}' for doc_id: {doc_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving query '{query_name}' for doc_id {doc_id}: {e}")
        return False

def save_report(conn: duckdb.DuckDBPyConnection, doc_id: str, 
                document_type: str, document_type_code: str,
                report_name: str, sql: str = "", sql_hash: str = "",
                is_global: bool = False, filters: Dict[str, Any] = None, 
                group_by: List[str] = None, format: str = "table",
                chart: str = "", output_type: str = "html", 
                description: str = "") -> bool:
    """
    Save a report to the saved_reports table with intelligent classification
    
    Stores report configuration in DuckDB with document type awareness and global/local
    classification. This enables intelligent report reuse across similar document types
    and prevents duplicate reports with different names.
    
    Args:
        conn: DuckDB connection for database operations
        doc_id: Document identifier for the source document
        document_type: Document type name (e.g., "Employee Data")
        document_type_code: Document type code (e.g., "EMP")
        report_name: Name of the report (generated by LLM or fallback)
        sql: SQL query used to generate report
        sql_hash: MD5 hash of normalized SQL for uniqueness detection
        is_global: True if saved globally for reuse, False if doc-specific only
        filters: Dictionary of filters applied (optional)
        group_by: List of fields to group by (optional)
        format: Report format (table, chart, etc.)
        chart: Chart type (bar, line, pie, etc.)
        output_type: Output format (html, xlsx, json)
        description: Optional description of the report
        
    Returns:
        bool: True if save successful, False otherwise
        
    Example:
        success = save_report(
            conn, "hospital_ledger_fy2024_001", "Financial Data", "FIN",
            "Weekly Vendor Spend", "SELECT Week, SUM(Amount) FROM hospital_ledger_fy2024_001 GROUP BY Week",
            "abc123hash", True, {"vendor": "Vendor X"}, ["Week"], "chart", "bar", "html"
        )
    """
    try:
        # Ensure saved_reports table exists
        create_report_table(conn)
        
        # Convert complex objects to JSON strings
        filters_json = json.dumps(filters) if filters else "{}"
        group_by_json = json.dumps(group_by) if group_by else "[]"
        
        # Get next available ID
        next_id_result = conn.execute("""
            SELECT COALESCE(MAX(id), 0) + 1 FROM saved_reports
        """).fetchone()
        next_id = next_id_result[0] if next_id_result else 1
        
        # Insert report record with intelligent classification fields
        conn.execute("""
            INSERT INTO saved_reports (id, doc_id, document_type, document_type_code, 
                                     report_name, sql, sql_hash, is_global, filters, group_by, 
                                     format, chart, output_type, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [next_id, doc_id, document_type, document_type_code, report_name, 
              sql, sql_hash, is_global, filters_json, group_by_json, 
              format, chart, output_type, description])
        
        logger.info(f"Successfully saved report '{report_name}' for doc_id: {doc_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving report '{report_name}' for doc_id {doc_id}: {e}")
        return False

def get_saved_queries(conn: duckdb.DuckDBPyConnection, doc_id: str = None, 
                     doc_ids: List[str] = None, tags: List[str] = None, 
                     date_range: Dict[str, str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve saved queries with optional filtering
    
    Searches the saved_queries table based on provided filters and returns
    matching query records.
    
    Args:
        conn: DuckDB connection
        doc_id: Filter by single document ID (optional)
        doc_ids: Filter by multiple document IDs (optional)
        tags: Filter by tags (optional)
        date_range: Filter by date range with 'start' and 'end' keys (optional)
        
    Returns:
        List[Dict[str, Any]]: List of matching query records
        
    Example:
        queries = get_saved_queries(
            conn, doc_id="hospital_ledger_fy2024_001", 
            tags=["vendor"], 
            date_range={"start": "2025-01-01", "end": "2025-01-31"}
        )
    """
    try:
        # Build WHERE clause based on filters
        where_conditions = []
        params = []
        
        if doc_id:
            where_conditions.append("doc_id = ?")
            params.append(doc_id)
        elif doc_ids:
            # Handle multiple doc_ids
            placeholders = ','.join(['?' for _ in doc_ids])
            where_conditions.append(f"doc_id IN ({placeholders})")
            params.extend(doc_ids)
        
        if tags:
            # Search for any of the provided tags in the JSON tags field
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags LIKE ?")
                params.append(f"%{tag}%")
            if tag_conditions:
                where_conditions.append(f"({' OR '.join(tag_conditions)})")
        
        if date_range:
            if 'start' in date_range:
                where_conditions.append("created_date >= ?")
                params.append(date_range['start'])
            if 'end' in date_range:
                where_conditions.append("created_date <= ?")
                params.append(date_range['end'])
        
        # Build complete query
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
            SELECT id, doc_id, query_name, query_text, sql, tags, 
                   created_date, last_used, use_count, description
            FROM saved_queries
            {where_clause}
            ORDER BY created_date DESC
        """
        
        # Execute query
        result = conn.execute(query, params).fetchall()
        
        # Convert to list of dictionaries
        queries = []
        for row in result:
            queries.append({
                "id": row[0],
                "doc_id": row[1],
                "query_name": row[2],
                "query_text": row[3],
                "sql": row[4],
                "tags": json.loads(row[5]) if row[5] else [],
                "created_date": row[6],
                "last_used": row[7],
                "use_count": row[8],
                "description": row[9]
            })
        
        logger.info(f"Retrieved {len(queries)} saved queries")
        return queries
        
    except Exception as e:
        logger.error(f"Error retrieving saved queries: {e}")
        return []

def get_saved_reports(conn: duckdb.DuckDBPyConnection, doc_id: str = None,
                     doc_ids: List[str] = None, tags: List[str] = None, 
                     output_type: str = None) -> List[Dict[str, Any]]:
    """
    Retrieve saved reports with optional filtering
    
    Searches the saved_reports table based on provided filters and returns
    matching report records.
    
    Args:
        conn: DuckDB connection
        doc_id: Filter by single document ID (optional)
        doc_ids: Filter by multiple document IDs (optional)
        tags: Filter by tags in report name or description (optional)
        output_type: Filter by output type (optional)
        
    Returns:
        List[Dict[str, Any]]: List of matching report records
        
    Example:
        reports = get_saved_reports(
            conn, doc_id="hospital_ledger_fy2024_001", 
            output_type="html"
        )
    """
    try:
        # Build WHERE clause based on filters
        where_conditions = []
        params = []
        
        if doc_id:
            where_conditions.append("doc_id = ?")
            params.append(doc_id)
        elif doc_ids:
            # Handle multiple doc_ids
            placeholders = ','.join(['?' for _ in doc_ids])
            where_conditions.append(f"doc_id IN ({placeholders})")
            params.extend(doc_ids)
        
        if tags:
            # Search for any of the provided tags in report name or description
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("(report_name LIKE ? OR description LIKE ?)")
                params.extend([f"%{tag}%", f"%{tag}%"])
            if tag_conditions:
                where_conditions.append(f"({' OR '.join(tag_conditions)})")
        
        if output_type:
            where_conditions.append("output_type = ?")
            params.append(output_type)
        
        # Build complete query
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
            SELECT id, doc_id, report_name, sql, filters, group_by, 
                   format, chart, output_type, description, created_date, 
                   last_generated, generation_count
            FROM saved_reports
            {where_clause}
            ORDER BY created_date DESC
        """
        
        # Execute query
        result = conn.execute(query, params).fetchall()
        
        # Convert to list of dictionaries
        reports = []
        for row in result:
            reports.append({
                "id": row[0],
                "doc_id": row[1],
                "report_name": row[2],
                "sql": row[3],
                "filters": json.loads(row[4]) if row[4] else {},
                "group_by": json.loads(row[5]) if row[5] else [],
                "format": row[6],
                "chart": row[7],
                "output_type": row[8],
                "description": row[9],
                "created_date": row[10],
                "last_generated": row[11],
                "generation_count": row[12]
            })
        
        logger.info(f"Retrieved {len(reports)} saved reports")
        return reports
        
    except Exception as e:
        logger.error(f"Error retrieving saved reports: {e}")
        return []

def ensure_all_tables_exist() -> bool:
    """
    Ensure all required tables exist in the database
    
    Creates all necessary tables for the AutoGen system:
    - doc_registry (from base duckdb_manager)
    - saved_queries (new)
    - saved_reports (new)
    
    Returns:
        bool: True if all tables created successfully
        
    Example:
        success = ensure_all_tables_exist()
        if success:
            print("All required tables are ready")
    """
    try:
        # Create database connection
        conn = create_persistent_database()
        
        # Import and create doc_registry table
        from duckdb_manager import create_document_registry_table
        doc_registry_success = create_document_registry_table(conn)
        
        # Create new tables
        queries_success = create_query_table(conn)
        reports_success = create_report_table(conn)
        
        # Close connection
        conn.close()
        
        # Check all results
        all_success = doc_registry_success and queries_success and reports_success
        
        if all_success:
            logger.info("All required tables created successfully")
        else:
            logger.error("Some tables failed to create")
        
        return all_success
        
    except Exception as e:
        logger.error(f"Error ensuring all tables exist: {e}")
        return False

# Import json module for JSON operations
import json

def get_query_by_id(conn: duckdb.DuckDBPyConnection, query_id: int) -> Dict[str, Any]:
    """
    Retrieve a specific query by its ID
    
    Args:
        conn: DuckDB connection
        query_id: The ID of the query to retrieve
        
    Returns:
        Dict with query details or None if not found
    """
    try:
        # Ensure saved_queries table exists
        create_query_table(conn)
        
        # Query for the specific query ID
        result = conn.execute("""
            SELECT id, doc_id, query_name, sql, query_text, tags, 
                   created_date, use_count, last_used
            FROM saved_queries 
            WHERE id = ?
        """, [query_id]).fetchone()
        
        if result:
            return {
                "id": result[0],
                "doc_id": result[1],
                "query_name": result[2],
                "sql": result[3],
                "query_text": result[4],
                "tags": result[5],
                "created_timestamp": result[6],  # Map created_date to created_timestamp for consistency
                "use_count": result[7],
                "last_used": result[8]
            }
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving query by ID {query_id}: {e}")
        return None

def get_query_by_name(conn: duckdb.DuckDBPyConnection, query_name: str) -> Dict[str, Any]:
    """
    Retrieve a specific query by its name
    
    Args:
        conn: DuckDB connection
        query_name: The name of the query to retrieve
        
    Returns:
        Dict with query details or None if not found
    """
    try:
        # Ensure saved_queries table exists
        create_query_table(conn)
        
        # Query for the specific query name
        result = conn.execute("""
            SELECT id, doc_id, query_name, sql, query_text, tags, 
                   created_date, use_count, last_used
            FROM saved_queries 
            WHERE query_name = ?
        """, [query_name]).fetchone()
        
        if result:
            return {
                "id": result[0],
                "doc_id": result[1],
                "query_name": result[2],
                "sql": result[3],
                "query_text": result[4],
                "tags": result[5],
                "created_timestamp": result[6],  # Map created_date to created_timestamp for consistency
                "use_count": result[7],
                "last_used": result[8]
            }
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving query by name '{query_name}': {e}")
        return None

def update_query_usage_stats(conn: duckdb.DuckDBPyConnection, query_id: int) -> bool:
    """
    Update usage statistics for a query (use_count and last_used timestamp)
    
    Args:
        conn: DuckDB connection
        query_id: The ID of the query to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure saved_queries table exists
        create_query_table(conn)
        
        # Update usage statistics
        conn.execute("""
            UPDATE saved_queries 
            SET use_count = COALESCE(use_count, 0) + 1,
                last_used = CURRENT_TIMESTAMP
            WHERE id = ?
        """, [query_id])
        
        logger.info(f"Updated usage stats for query ID: {query_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating usage stats for query {query_id}: {e}")
        return False

def get_report_by_id(conn: duckdb.DuckDBPyConnection, report_id: int) -> Dict[str, Any]:
    """
    Retrieve a specific report by its ID
    
    Args:
        conn: DuckDB connection
        report_id: The ID of the report to retrieve
        
    Returns:
        Dict with report details or None if not found
    """
    try:
        # Ensure saved_reports table exists
        create_report_table(conn)
        
        # Query for the specific report ID
        result = conn.execute("""
            SELECT id, doc_id, report_name, sql, filters, group_by, 
                   format, chart, output_type, description, created_timestamp,
                   generation_count, last_generated
            FROM saved_reports 
            WHERE id = ?
        """, [report_id]).fetchone()
        
        if result:
            return {
                "id": result[0],
                "doc_id": result[1],
                "report_name": result[2],
                "sql": result[3],
                "filters": result[4],
                "group_by": result[5],
                "format": result[6],
                "chart": result[7],
                "output_type": result[8],
                "description": result[9],
                "created_timestamp": result[10],
                "generation_count": result[11],
                "last_generated": result[12]
            }
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving report by ID {report_id}: {e}")
        return None

def update_report_usage_stats(conn: duckdb.DuckDBPyConnection, report_id: int) -> bool:
    """
    Update usage statistics for a report (generation_count and last_generated timestamp)
    
    Args:
        conn: DuckDB connection
        report_id: The ID of the report to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure saved_reports table exists
        create_report_table(conn)
        
        # Update usage statistics
        conn.execute("""
            UPDATE saved_reports 
            SET generation_count = COALESCE(generation_count, 0) + 1,
                last_generated = CURRENT_TIMESTAMP
            WHERE id = ?
        """, [report_id])
        
        logger.info(f"Updated usage stats for report ID: {report_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating usage stats for report {report_id}: {e}")
        return False

def check_sql_uniqueness(conn: duckdb.DuckDBPyConnection, sql: str, 
                        document_type_code: str) -> Dict[str, Any]:
    """
    Check if SQL query is unique within a document type
    
    This function normalizes SQL by removing table names, whitespace, and case differences
    to detect semantically identical queries across different documents. This enables
    intelligent query reuse and prevents duplicate queries with different names.
    
    Args:
        conn: DuckDB connection for database queries
        sql: SQL query to check for uniqueness
        document_type_code: Document type code (e.g., "EMP", "SALES") to scope the search
        
    Returns:
        Dict with uniqueness results and existing query info if found:
        - is_unique: Boolean indicating if query is unique
        - sql_hash: MD5 hash of normalized SQL for future comparisons
        - existing_query: Dict with existing query details if not unique
        - error: Error message if uniqueness check failed
        
    Example:
        result = check_sql_uniqueness(conn, "SELECT * FROM employees WHERE years >= 5", "EMP")
        if result["is_unique"]:
            print("Query is unique - can be saved globally")
        else:
            print(f"Query exists: {result['existing_query']['query_name']}")
    """
    try:
        # Normalize SQL for comparison to detect semantically identical queries
        normalized_sql = normalize_sql_for_comparison(sql)
        sql_hash = hashlib.md5(normalized_sql.encode()).hexdigest()
        
        # Check if this SQL pattern exists for this document type
        # Only check globally saved queries (is_global = TRUE) to avoid duplicates
        existing_query = conn.execute("""
            SELECT id, query_name, doc_id, description, use_count
            FROM saved_queries 
            WHERE sql_hash = ? AND document_type_code = ? AND is_global = TRUE
            ORDER BY use_count DESC, created_date DESC
            LIMIT 1
        """, [sql_hash, document_type_code]).fetchone()
        
        if existing_query:
            # Query already exists - return existing query details
            return {
                "is_unique": False,
                "existing_query": {
                    "id": existing_query[0],
                    "query_name": existing_query[1],
                    "doc_id": existing_query[2],
                    "description": existing_query[3],
                    "use_count": existing_query[4]
                },
                "sql_hash": sql_hash
            }
        else:
            # Query is unique - safe to save globally
            return {
                "is_unique": True,
                "sql_hash": sql_hash
            }
            
    except Exception as e:
        logger.error(f"Error checking SQL uniqueness: {e}")
        return {"is_unique": True, "sql_hash": "", "error": str(e)}

def normalize_sql_for_comparison(sql: str) -> str:
    """
    Normalize SQL for uniqueness comparison
    
    This function removes table names, normalizes whitespace, converts to lowercase,
    and standardizes formatting to detect semantically identical queries. This allows
    the system to recognize that "SELECT * FROM employees WHERE years >= 5" and
    "select * from staff where years >= 5" are the same query pattern.
    
    Args:
        sql: Raw SQL query to normalize
        
    Returns:
        str: Normalized SQL string for comparison
        
    Example:
        normalized = normalize_sql_for_comparison("SELECT * FROM employees WHERE years >= 5")
        # Returns: "select * from [table] where [column] = [number]"
    """
    # Convert to lowercase for case-insensitive comparison
    normalized = sql.lower().strip()
    
    # Remove extra whitespace and normalize spacing
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Replace table names with placeholder to focus on query structure
    # Pattern: FROM table_name, JOIN table_name, UPDATE table_name, etc.
    table_patterns = [
        r'from\s+[a-zA-Z_][a-zA-Z0-9_]*',
        r'join\s+[a-zA-Z_][a-zA-Z0-9_]*',
        r'update\s+[a-zA-Z_][a-zA-Z0-9_]*',
        r'insert\s+into\s+[a-zA-Z_][a-zA-Z0-9_]*',
        r'delete\s+from\s+[a-zA-Z_][a-zA-Z0-9_]*'
    ]
    
    for pattern in table_patterns:
        # Replace table names with generic placeholder while keeping SQL structure
        normalized = re.sub(pattern, lambda m: m.group(0).split()[0] + ' [TABLE]', normalized)
    
    # Remove specific values in WHERE clauses to focus on query structure
    # This allows "WHERE years >= 5" and "WHERE years >= 10" to be recognized as similar
    normalized = re.sub(r"where\s+[^=]+=\s*'[^']*'", 'where [COLUMN] = [VALUE]', normalized)
    normalized = re.sub(r"where\s+[^=]+=\s*\d+", 'where [COLUMN] = [NUMBER]', normalized)
    
    return normalized
