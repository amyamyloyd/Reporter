# Query and Report Classification Implementation Plan

## Overview

This document outlines the intelligent classification approach for queries and reports that mirrors the document classification logic. The goal is to automatically detect unique SQL patterns, generate meaningful names using LLM, and save them appropriately based on document type and SQL uniqueness.

## Current vs. Proposed Architecture

### Current Flow
1. **Query/Report Generated** → Auto-save with fallback name ("temp_query", "temp_report")
2. **Manual Save** → User provides name via `/save_query` or `/save_report`
3. **No Uniqueness Detection** → Same SQL can be saved multiple times with different names
4. **No Document Type Awareness** → Queries tied only to specific doc_id

### Proposed Intelligent Flow
1. **Query/Report Generated** → Check SQL uniqueness within document type
2. **If Unique** → Call LLM to generate meaningful name → Save to both doc-specific JSON and global registry
3. **If Not Unique** → Save only to doc-specific JSON (no global registry)
4. **Document Type Awareness** → Queries/reports can be reused across same document types

## Key Changes

### 1. Add Document Type Fields to Database Tables

**Location**: `backend/utils/duckdb_manager.py` - `create_query_table()` and `create_report_table()`

**Current Structure**:
```sql
CREATE TABLE saved_queries (
    id INTEGER PRIMARY KEY,
    doc_id VARCHAR NOT NULL,
    query_name VARCHAR NOT NULL,
    query_text TEXT NOT NULL,
    sql TEXT NOT NULL,
    tags TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    use_count INTEGER DEFAULT 0,
    description TEXT
)
```

**New Structure**:
```sql
CREATE TABLE saved_queries (
    id INTEGER PRIMARY KEY,
    doc_id VARCHAR NOT NULL,
    document_type VARCHAR,  -- NEW: Document type (e.g., "Employee Data")
    document_type_code VARCHAR,  -- NEW: Document type code (e.g., "EMP")
    query_name VARCHAR NOT NULL,
    query_text TEXT NOT NULL,
    sql TEXT NOT NULL,
    sql_hash VARCHAR,  -- NEW: Hash of normalized SQL for uniqueness detection
    is_global BOOLEAN DEFAULT FALSE,  -- NEW: True if saved globally, False if doc-specific only
    tags TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    use_count INTEGER DEFAULT 0,
    description TEXT
)
```

**Similar changes for saved_reports table**

### 2. Create SQL Uniqueness Detection Function

**New Function**: `check_sql_uniqueness()` in `backend/utils/duckdb_manager.py`

```python
def check_sql_uniqueness(conn: duckdb.DuckDBPyConnection, sql: str, 
                        document_type_code: str) -> Dict[str, Any]:
    """
    Check if SQL query is unique within a document type
    
    Normalizes SQL by removing table names, whitespace, and case differences
    to detect semantically identical queries across different documents.
    
    Args:
        conn: DuckDB connection
        sql: SQL query to check
        document_type_code: Document type code (e.g., "EMP", "SALES")
        
    Returns:
        Dict with uniqueness results and existing query info if found
    """
    try:
        # Normalize SQL for comparison
        normalized_sql = normalize_sql_for_comparison(sql)
        sql_hash = hashlib.md5(normalized_sql.encode()).hexdigest()
        
        # Check if this SQL pattern exists for this document type
        existing_query = conn.execute("""
            SELECT id, query_name, doc_id, description, use_count
            FROM saved_queries 
            WHERE sql_hash = ? AND document_type_code = ? AND is_global = TRUE
            ORDER BY use_count DESC, created_date DESC
            LIMIT 1
        """, [sql_hash, document_type_code]).fetchone()
        
        if existing_query:
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
    
    Removes table names, normalizes whitespace, converts to lowercase,
    and standardizes formatting to detect semantically identical queries.
    """
    import re
    
    # Convert to lowercase
    normalized = sql.lower().strip()
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Replace table names with placeholder
    # Pattern: FROM table_name, JOIN table_name, UPDATE table_name, etc.
    table_patterns = [
        r'from\s+[a-zA-Z_][a-zA-Z0-9_]*',
        r'join\s+[a-zA-Z_][a-zA-Z0-9_]*',
        r'update\s+[a-zA-Z_][a-zA-Z0-9_]*',
        r'insert\s+into\s+[a-zA-Z_][a-zA-Z0-9_]*',
        r'delete\s+from\s+[a-zA-Z_][a-zA-Z0-9_]*'
    ]
    
    for pattern in table_patterns:
        normalized = re.sub(pattern, lambda m: m.group(0).split()[0] + ' [TABLE]', normalized)
    
    # Remove specific values in WHERE clauses (keep structure)
    normalized = re.sub(r"where\s+[^=]+=\s*'[^']*'", 'where [COLUMN] = [VALUE]', normalized)
    normalized = re.sub(r"where\s+[^=]+=\s*\d+", 'where [COLUMN] = [NUMBER]', normalized)
    
    return normalized
```

### 3. Create LLM Query/Report Naming Function

**New Function**: `generate_query_name_with_llm()` in `backend/app.py`

```python
async def generate_query_name_with_llm(sql: str, query_text: str, 
                                     document_type: str, document_type_code: str) -> Dict[str, Any]:
    """
    Generate meaningful query name using OpenAI LLM
    
    Analyzes the SQL query and natural language text to create a professional,
    descriptive name that reflects the query's purpose and business value.
    
    Args:
        sql: Generated SQL query
        query_text: Original natural language query
        document_type: Document type (e.g., "Employee Data")
        document_type_code: Document type code (e.g., "EMP")
        
    Returns:
        Dict with generated name and description
    """
    try:
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        system_prompt = f"""You are an expert at creating professional, descriptive names for database queries.

Analyze the SQL query and natural language description to create a meaningful name that:
1. Reflects the business purpose of the query
2. Is professional and clear
3. Is concise but descriptive (2-6 words)
4. Avoids technical jargon when possible
5. Focuses on the business value, not the technical implementation

Document Type: {document_type} ({document_type_code})

Guidelines:
- Use business terminology that users would understand
- Focus on what the query reveals, not how it works
- Examples:
  * "SELECT * FROM employees WHERE years >= 5" → "Senior Employees"
  * "SELECT SUM(amount) FROM sales WHERE quarter = 'Q1'" → "Q1 Revenue Summary"
  * "SELECT COUNT(*) FROM orders WHERE status = 'pending'" → "Pending Orders Count"
  * "SELECT AVG(salary) FROM employees GROUP BY department" → "Department Salary Averages"

Return your response as valid JSON with these exact fields:
{{
  "query_name": "Professional Query Name",
  "description": "Brief description of what this query reveals or calculates"
}}"""

        user_prompt = f"""Please create a professional name for this query:

Natural Language Query: {query_text}
SQL Query: {sql}
Document Type: {document_type}

Focus on the business value and what insights this query provides."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=150,
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content.strip()
        result = json.loads(ai_response)
        
        # Validate required fields
        if "query_name" not in result or "description" not in result:
            raise ValueError("Missing required fields in LLM response")
        
        return {
            "success": True,
            "query_name": result["query_name"],
            "description": result["description"],
            "ai_response": ai_response
        }
        
    except Exception as e:
        logger.error(f"LLM query naming failed: {e}")
        
        # FALLBACK: Generate name from SQL structure
        fallback_name = generate_fallback_query_name(sql, query_text)
        
        return {
            "success": False,
            "fallback": True,
            "query_name": fallback_name,
            "description": f"Query for {document_type}: {query_text[:50]}...",
            "error": str(e)
        }

def generate_fallback_query_name(sql: str, query_text: str) -> str:
    """Generate fallback query name when LLM fails"""
    import re
    
    # Extract key operations
    if "COUNT" in sql.upper():
        return "Record Count"
    elif "SUM" in sql.upper():
        return "Total Amount"
    elif "AVG" in sql.upper():
        return "Average Value"
    elif "MAX" in sql.upper():
        return "Maximum Value"
    elif "MIN" in sql.upper():
        return "Minimum Value"
    elif "GROUP BY" in sql.upper():
        return "Grouped Analysis"
    elif "WHERE" in sql.upper():
        return "Filtered Data"
    else:
        return "Data Query"
```

### 4. Update Query Endpoint Logic

**Location**: `backend/app.py` - `/query` endpoint (lines 2552-2703)

**Current Logic**:
```python
# Auto-save query with fallback name "temp_query" (as specified)
query_name = request.get("query_name", "temp_query")
tags = request.get("tags", [])

save_success = save_query(
    conn=conn,
    doc_id=doc_id,
    query_name=query_name,
    query_text=query_text,
    sql=sql_query,
    tags=tags,
    description=f"Auto-generated from: {query_text}"
)
```

**New Logic**:
```python
# Get document type information
doc_metadata = load_metadata(doc_id)
document_type = doc_metadata.get("document_type", "Unknown")
document_type_code = doc_metadata.get("document_type_code", "UNK")

# Check SQL uniqueness within document type
uniqueness_result = check_sql_uniqueness(conn, sql_query, document_type_code)

if uniqueness_result["is_unique"]:
    # SQL is unique - generate meaningful name and save globally
    naming_result = await generate_query_name_with_llm(
        sql_query, query_text, document_type, document_type_code
    )
    
    if naming_result["success"]:
        query_name = naming_result["query_name"]
        description = naming_result["description"]
    else:
        # Use fallback name
        query_name = naming_result["query_name"]
        description = naming_result["description"]
    
    # Save globally (is_global = TRUE)
    save_success = save_query(
        conn=conn,
        doc_id=doc_id,
        document_type=document_type,
        document_type_code=document_type_code,
        query_name=query_name,
        query_text=query_text,
        sql=sql_query,
        sql_hash=uniqueness_result["sql_hash"],
        is_global=True,
        tags=tags,
        description=description
    )
    
    logger.info(f"✅ Unique query saved globally: {query_name}")
    
else:
    # SQL already exists - save only to document-specific JSON
    existing_query = uniqueness_result["existing_query"]
    query_name = f"temp_query_{doc_id}_{int(time.time())}"
    
    # Save locally only (is_global = FALSE)
    save_success = save_query(
        conn=conn,
        doc_id=doc_id,
        document_type=document_type,
        document_type_code=document_type_code,
        query_name=query_name,
        query_text=query_text,
        sql=sql_query,
        sql_hash=uniqueness_result["sql_hash"],
        is_global=False,
        tags=tags,
        description=f"Local copy of: {existing_query['query_name']}"
    )
    
    logger.info(f"📋 Duplicate query saved locally: {query_name} (similar to: {existing_query['query_name']})")
```

### 5. Update Report Endpoint Logic

**Location**: `backend/app.py` - `/report` endpoint (lines 2904-3086)

**Similar logic to queries but for reports**:
- Check SQL uniqueness within document type
- If unique: Generate meaningful name with LLM, save globally
- If not unique: Save only to document-specific JSON
- Include document type fields in save_report function

### 6. Update Save Functions

**Location**: `backend/utils/duckdb_manager.py` - `save_query()` and `save_report()`

**Add new parameters**:
```python
def save_query(conn: duckdb.DuckDBPyConnection, doc_id: str, 
               document_type: str, document_type_code: str,
               query_name: str, query_text: str, sql: str, 
               sql_hash: str, is_global: bool,
               tags: List[str] = None, description: str = "") -> bool:
```

**Update SQL INSERT**:
```sql
INSERT INTO saved_queries (id, doc_id, document_type, document_type_code, 
                          query_name, query_text, sql, sql_hash, is_global, 
                          tags, description)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
```

## Benefits

### 1. **Intelligent Naming**
- LLM generates meaningful, professional query/report names
- Names reflect business value, not technical implementation
- Consistent naming across similar queries

### 2. **Uniqueness Detection**
- Prevents duplicate queries with different names
- Enables query reuse across same document types
- Reduces database bloat

### 3. **Document Type Awareness**
- Queries can be reused across different documents of same type
- Employee queries work for all employee datasets
- Sales queries work for all sales datasets

### 4. **Smart Storage Strategy**
- Unique queries: Saved globally for reuse
- Duplicate queries: Saved locally only
- Efficient storage and retrieval

## User Case Example

**Scenario**: User uploads employee data, asks "list all employees that have worked here for over five years"

**Current Flow**:
1. SQL generated: `SELECT * FROM employees WHERE years >= 5`
2. Saved as: "temp_query" (generic name)
3. No reuse possible

**New Flow**:
1. SQL generated: `SELECT * FROM employees WHERE years >= 5`
2. Check uniqueness: SQL is unique for "Employee Data" type
3. LLM generates name: "Senior Employees"
4. Saved globally as reusable query
5. Future employee datasets can reuse this query

## Files to Modify

### 1. **`backend/utils/duckdb_manager.py`**
- Add `document_type`, `document_type_code`, `sql_hash`, `is_global` fields to tables
- Create `check_sql_uniqueness()` function
- Create `normalize_sql_for_comparison()` function
- Update `save_query()` and `save_report()` functions

### 2. **`backend/app.py`**
- Create `generate_query_name_with_llm()` function
- Create `generate_report_name_with_llm()` function
- Update `/query` endpoint logic
- Update `/report` endpoint logic

### 3. **Database Migration**
- Add new columns to existing `saved_queries` and `saved_reports` tables
- Populate `document_type` and `document_type_code` for existing records

## Implementation Priority

1. **Phase 1**: Add database schema changes
2. **Phase 2**: Implement SQL uniqueness detection
3. **Phase 3**: Create LLM naming functions
4. **Phase 4**: Update query endpoint logic
5. **Phase 5**: Update report endpoint logic
6. **Phase 6**: Test with various SQL patterns
7. **Phase 7**: Migrate existing data

## Testing Scenarios

### Test Cases
1. **Unique Query**: New SQL pattern → LLM naming → Global save
2. **Duplicate Query**: Existing SQL pattern → Local save only
3. **Cross-Document Reuse**: Same document type, different doc_id
4. **LLM Failure**: Fallback naming works
5. **SQL Normalization**: Similar queries detected as duplicates

### Sample Test Queries
- `SELECT * FROM employees WHERE years >= 5` → "Senior Employees"
- `SELECT SUM(salary) FROM employees GROUP BY department` → "Department Salary Totals"
- `SELECT COUNT(*) FROM orders WHERE status = 'pending'` → "Pending Orders Count"

## Conclusion

This intelligent classification approach transforms queries and reports from simple storage to smart, reusable business assets. By detecting uniqueness and generating meaningful names, the system becomes more valuable and user-friendly while reducing redundancy and enabling cross-dataset query reuse.
