# Data Architecture Blueprint - Excel Reporting POC

## Overview
Comprehensive data model documentation for the Excel Reporting POC system. This blueprint provides detailed information about database schemas, entity relationships, data flow patterns, and business logic constraints for LangChain agent integration and AutoGen migration.

**Database Engine**: DuckDB with persistent storage (`excel_reporting.db`)  
**Data Format**: Excel files → JSON metadata → DuckDB tables  
**Agent Integration**: Direct database access for queries and reports

---

## Database Schema Architecture

### Core System Tables

#### 1. **doc_registry** - Document Type Registry
**Purpose**: Store document types and field patterns for auto-classification

**Schema**:
```sql
CREATE TABLE doc_registry (
    id INTEGER PRIMARY KEY,
    document_type VARCHAR NOT NULL,                    -- Human-readable document type
    document_type_code VARCHAR NOT NULL,              -- Short code (e.g., 'EMP', 'FIN')
    field_pattern VARCHAR NOT NULL,                   -- Pipe-separated field names
    reuse_regularly BOOLEAN DEFAULT false,            -- Whether this type is commonly used
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description VARCHAR,                              -- Detailed description
    example_filename VARCHAR,                         -- Example file name
    latest_version VARCHAR DEFAULT '1.0',            -- Version tracking
    is_favorite BOOLEAN DEFAULT false                -- User favorite flag
);
```

**Indexes**:
- `UNIQUE(document_type)` - Ensure unique document types
- `INDEX(document_type_code)` - Fast lookup by code
- `INDEX(reuse_regularly)` - Filter commonly used types

**Sample Data**:
```sql
INSERT INTO doc_registry VALUES 
(5, 'Test Product Catalog', 'TPC', 'Category|Name|Price|Product_ID', true, '2025-09-01 11:53:59', '2025-09-01 11:55:38', 'Test product catalog', NULL, '5.0', false),
(6, 'Test Employee Directory', 'TED', 'Department|Employee_ID|Name|Salary', true, '2025-09-01 11:55:19', '2025-09-01 11:55:38', 'Test employee data', NULL, '3.0', false),
(7, 'Hotel Discount Information', 'HDI', 'Discount Rate|Hotel Name|Location (city)', true, '2025-09-06 11:11:10', '2025-09-06 13:04:44', 'This document provides information about various hotels, their locations, and the discount rates they offer.', NULL, '3.0', false);
```

**Business Rules**:
- Document types are immutable once created
- Field patterns must be pipe-separated (`|`) for parsing
- Version tracking enables document evolution
- Favorites enable quick access to common types

---

#### 2. **saved_queries** - Query Persistence
**Purpose**: Store saved SQL queries for reuse and navigation

**Schema**:
```sql
CREATE TABLE saved_queries (
    id INTEGER PRIMARY KEY,
    doc_id VARCHAR NOT NULL,                          -- Document identifier
    query_name VARCHAR NOT NULL,                      -- User-friendly query name
    query_text VARCHAR NOT NULL,                      -- Original natural language query
    sql VARCHAR NOT NULL,                             -- Generated SQL query
    tags VARCHAR,                                     -- Comma-separated tags
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,                              -- Last execution timestamp
    use_count INTEGER DEFAULT 0,                      -- Usage counter
    description VARCHAR,                              -- Query description
    document_type VARCHAR,                            -- Associated document type
    document_type_code VARCHAR,                       -- Document type code
    sql_hash VARCHAR,                                 -- SQL hash for deduplication
    is_global BOOLEAN DEFAULT false,                  -- Available across all documents
    is_favorite BOOLEAN DEFAULT false                -- User favorite flag
);
```

**Indexes**:
- `INDEX(doc_id)` - Fast lookup by document
- `INDEX(query_name)` - Fast lookup by name
- `INDEX(document_type_code)` - Filter by document type
- `INDEX(is_favorite)` - Filter favorites
- `INDEX(sql_hash)` - Deduplication

**Sample Data**:
```sql
INSERT INTO saved_queries VALUES 
(1, 'financial_data_2025-09-01_114904', 'total_transactions', 'How many transactions do we have?', 'SELECT COUNT(*) as total_transactions FROM financial_data_20250901_114904', 'summary,count', '2025-09-02 17:41:05', '2025-09-02 17:41:05', 1, 'Count of all transactions', 'Financial Data', 'FIN', 'abc123', false, false),
(2, 'financial_data_2025-09-01_114904', 'high_value_transactions', 'Show me transactions over $1000', 'SELECT * FROM financial_data_20250901_114904 WHERE Amount > 1000', 'high-value,filter', '2025-09-02 17:41:12', '2025-09-02 17:41:12', 1, 'High value transaction filter', 'Financial Data', 'FIN', 'def456', false, false);
```

**Business Rules**:
- Query names must be unique per document
- SQL queries are validated before saving
- Use count tracks query popularity
- Global queries are available across all documents

---

#### 3. **saved_reports** - Report Persistence
**Purpose**: Store saved report configurations for reuse and navigation

**Schema**:
```sql
CREATE TABLE saved_reports (
    id INTEGER PRIMARY KEY,
    doc_id VARCHAR NOT NULL,                          -- Document identifier
    report_name VARCHAR NOT NULL,                     -- User-friendly report name
    sql VARCHAR NOT NULL,                             -- Generated SQL query
    filters VARCHAR,                                  -- JSON string of filter criteria
    group_by VARCHAR,                                 -- JSON string of grouping fields
    format VARCHAR,                                   -- Output format (HTML, XLSX, JSON)
    chart VARCHAR,                                    -- Chart type (bar, line, pie)
    output_type VARCHAR,                              -- Report output type
    description VARCHAR,                              -- Report description
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_generated TIMESTAMP,                         -- Last generation timestamp
    generation_count INTEGER DEFAULT 0,               -- Generation counter
    document_type VARCHAR,                            -- Associated document type
    document_type_code VARCHAR,                       -- Document type code
    sql_hash VARCHAR,                                 -- SQL hash for deduplication
    is_global BOOLEAN DEFAULT false,                  -- Available across all documents
    is_favorite BOOLEAN DEFAULT false                -- User favorite flag
);
```

**Indexes**:
- `INDEX(doc_id)` - Fast lookup by document
- `INDEX(report_name)` - Fast lookup by name
- `INDEX(document_type_code)` - Filter by document type
- `INDEX(is_favorite)` - Filter favorites
- `INDEX(sql_hash)` - Deduplication

**Sample Data**:
```sql
INSERT INTO saved_reports VALUES 
(1, 'financial_data_2025-09-01_114904', 'Transaction Type Summary', 'SELECT Transaction_Type, COUNT(*) as count, SUM(Amount) as total FROM financial_data_20250901_114904 GROUP BY Transaction_Type', '{"status": "completed"}', '["Transaction_Type"]', 'HTML', 'bar', 'summary', 'Summary of transactions by type', '2025-09-02 18:01:36', '2025-09-02 18:01:36', 1, 'Financial Data', 'FIN', 'ghi789', false, false);
```

**Business Rules**:
- Report names must be unique per document
- Filters and group_by stored as JSON strings
- Generation count tracks report usage
- Global reports available across all documents

---

### Dynamic Data Tables

#### Excel Data Tables
**Purpose**: Store uploaded Excel data with standardized naming

**Naming Convention**: `{filename}_{document_type_code}_{timestamp}`

**Examples**:
- `employees_20250906_114501` - Employee data uploaded on 2025-09-06 at 11:45:01
- `financial_data_20250901_114904` - Financial data uploaded on 2025-09-01 at 11:49:04
- `HospitalA_20250905_224846` - Hospital data uploaded on 2025-09-05 at 22:48:46

**Common Table Patterns**:

##### Employee Data Tables
```sql
-- Pattern: employees_YYYYMMDD_HHMMSS
CREATE TABLE employees_20250906_114501 (
    "First Name" VARCHAR,
    "Last Name" VARCHAR,
    "Location" VARCHAR,
    "Salary" BIGINT,
    "Years" BIGINT
);
```

##### Financial Data Tables
```sql
-- Pattern: financial_data_YYYYMMDD_HHMMSS
CREATE TABLE financial_data_20250901_114904 (
    "Transaction ID" BIGINT,
    "Company Code" VARCHAR,
    "Transaction Type" VARCHAR,
    "Amount" DOUBLE,
    "Transaction Date" TIMESTAMP_NS,
    "Category" VARCHAR,
    "Status" VARCHAR
);
```

##### Hospital Data Tables
```sql
-- Pattern: HospitalA_YYYYMMDD_HHMMSS
CREATE TABLE HospitalA_20250905_224846 (
    "Account Number" BIGINT,
    "Account Description" VARCHAR,
    "Classification" VARCHAR,
    "Entity" VARCHAR,
    "Cost Center Code" BIGINT,
    "Cost Center Desc" VARCHAR,
    "Asset Group" VARCHAR,
    "Month" VARCHAR,
    "Beginning Balance" BIGINT,
    "Debits" BIGINT,
    "Credits" BIGINT,
    "Net Change" BIGINT,
    "Ending Balance" BIGINT
);
```

---

## Entity Relationship Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   doc_registry  │    │  saved_queries  │    │  saved_reports  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ document_type   │    │ doc_id (FK)     │    │ doc_id (FK)     │
│ document_code   │    │ query_name      │    │ report_name     │
│ field_pattern   │    │ query_text      │    │ sql             │
│ description     │    │ sql             │    │ filters         │
│ version         │    │ tags            │    │ group_by        │
│ is_favorite     │    │ use_count       │    │ format          │
└─────────────────┘    │ is_favorite     │    │ generation_count│
                       └─────────────────┘    │ is_favorite     │
                                              └─────────────────┘
                                                       │
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  JSON Metadata  │    │  Excel Files    │    │  DuckDB Tables  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ doc_id          │◄───┤ filename        │    │ table_name      │
│ filename        │    │ content         │    │ columns         │
│ sheets          │    │ upload_time     │    │ data            │
│ fields          │    │ file_size       │    │ row_count       │
│ types           │    │ content_type    │    │ created_time    │
│ metadata        │    │ validation      │    │ last_accessed   │
│ conversation    │    │ status          │    │ access_count    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Relationships**:
- **doc_registry** → **saved_queries**: One-to-many (document_type_code)
- **doc_registry** → **saved_reports**: One-to-many (document_type_code)
- **JSON Metadata** → **Excel Files**: One-to-one (doc_id)
- **JSON Metadata** → **DuckDB Tables**: One-to-one (duckdb_table_name)
- **Excel Files** → **DuckDB Tables**: One-to-one (table_name)

---

## Data Flow Architecture

### 1. File Upload Flow
```
Excel File Upload
       │
       ▼
File Validation
       │
       ▼
Metadata Extraction
       │
       ▼
Document Classification
       │
       ▼
JSON Metadata Creation
       │
       ▼
DuckDB Table Creation
       │
       ▼
Agent Analysis
```

**Detailed Steps**:
1. **File Upload**: User uploads Excel file via `/upload` endpoint
2. **Validation**: File format, size, and content validation
3. **Metadata Extraction**: Extract sheets, fields, types using `excel_processor.py`
4. **Classification**: Determine document type using `doc_registry`
5. **JSON Creation**: Create metadata file in `stored_queries/`
6. **Table Creation**: Create DuckDB table with normalized column names
7. **Agent Analysis**: Process through AutoGen agents for field analysis

### 2. Query Processing Flow
```
Natural Language Query
       │
       ▼
Agent Processing
       │
       ▼
SQL Generation
       │
       ▼
Query Execution
       │
       ▼
Result Processing
       │
       ▼
Query Persistence
```

**Detailed Steps**:
1. **Query Input**: User provides natural language query
2. **Agent Processing**: QueryAgent processes intent and context
3. **SQL Generation**: LLM generates SQL from natural language
4. **Execution**: SQL executed via DuckDB
5. **Result Processing**: Format results for display
6. **Persistence**: Save query to `saved_queries` table

### 3. Report Generation Flow
```
Report Specification
       │
       ▼
Agent Processing
       │
       ▼
Report Configuration
       │
       ▼
SQL Generation
       │
       ▼
Data Aggregation
       │
       ▼
Format Generation
       │
       ▼
Report Persistence
```

**Detailed Steps**:
1. **Report Spec**: User specifies report requirements
2. **Agent Processing**: ReportAgent interprets requirements
3. **Configuration**: Create filters, grouping, formatting rules
4. **SQL Generation**: Generate SQL for data aggregation
5. **Data Processing**: Execute SQL and process results
6. **Format Generation**: Create HTML, XLSX, or JSON output
7. **Persistence**: Save report to `saved_reports` table

---

## Business Entity Definitions

### 1. **Document Entity**
**Purpose**: Represents an uploaded Excel file and its metadata

**Attributes**:
- `doc_id`: Unique identifier (format: `{filename}_{document_type_code}_{timestamp}`)
- `filename`: Original Excel filename
- `document_type`: Human-readable document type
- `document_type_code`: Short code for classification
- `fields`: List of field names from Excel
- `normalized_fields`: DuckDB-compatible field names
- `types`: Data types for each field
- `record_count`: Number of rows in the data
- `upload_timestamp`: When the file was uploaded
- `conversation_status`: Status of agent analysis
- `duckdb_table_name`: Name of the DuckDB table

**Business Rules**:
- Document IDs must be unique across the system
- Field names are normalized for SQL compatibility
- Document types are classified automatically
- Conversation status tracks agent processing

### 2. **Query Entity**
**Purpose**: Represents a saved SQL query for reuse

**Attributes**:
- `id`: Unique query identifier
- `doc_id`: Associated document identifier
- `query_name`: User-friendly name
- `query_text`: Original natural language query
- `sql`: Generated SQL query
- `tags`: Comma-separated tags for categorization
- `use_count`: Number of times executed
- `is_favorite`: User favorite flag
- `is_global`: Available across all documents

**Business Rules**:
- Query names must be unique per document
- SQL queries are validated before saving
- Use count tracks query popularity
- Global queries are available system-wide

### 3. **Report Entity**
**Purpose**: Represents a saved report configuration

**Attributes**:
- `id`: Unique report identifier
- `doc_id`: Associated document identifier
- `report_name`: User-friendly name
- `sql`: Generated SQL query
- `filters`: JSON string of filter criteria
- `group_by`: JSON string of grouping fields
- `format`: Output format (HTML, XLSX, JSON)
- `chart`: Chart type for visualization
- `generation_count`: Number of times generated
- `is_favorite`: User favorite flag
- `is_global`: Available across all documents

**Business Rules**:
- Report names must be unique per document
- Filters and grouping stored as JSON
- Generation count tracks usage
- Global reports available system-wide

---

## Data Validation Rules

### 1. **Document Validation**
```python
# Document ID format validation
def validate_doc_id(doc_id: str) -> bool:
    pattern = r'^[a-zA-Z0-9_]+_[A-Z]{2,4}_\d{8}_\d{6}$'
    return re.match(pattern, doc_id) is not None

# Field name normalization
def normalize_field_name(name: str) -> str:
    # Replace spaces and special chars with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    # Ensure starts with letter or underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = 'col_' + sanitized
    return sanitized.strip('_')[:64]
```

### 2. **Query Validation**
```python
# SQL query validation
def validate_sql_query(sql: str) -> bool:
    # Basic SQL syntax validation
    sql_keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING']
    sql_upper = sql.upper()
    return any(keyword in sql_upper for keyword in sql_keywords)

# Query name validation
def validate_query_name(name: str) -> bool:
    # Alphanumeric, spaces, hyphens, underscores only
    pattern = r'^[a-zA-Z0-9\s\-_]+$'
    return re.match(pattern, name) is not None and len(name) <= 100
```

### 3. **Report Validation**
```python
# Report configuration validation
def validate_report_config(config: dict) -> bool:
    required_fields = ['filters', 'group_by', 'format']
    return all(field in config for field in required_fields)

# Output format validation
def validate_output_format(format: str) -> bool:
    valid_formats = ['HTML', 'XLSX', 'JSON', 'CSV']
    return format.upper() in valid_formats
```

---

## Common Query Patterns

### 1. **Document Discovery Queries**
```sql
-- Get all document types
SELECT DISTINCT document_type, document_type_code 
FROM doc_registry 
WHERE reuse_regularly = true;

-- Get documents by type
SELECT doc_id, filename, record_count, upload_timestamp
FROM JSON metadata
WHERE document_type_code = 'EMP';

-- Get recent uploads
SELECT doc_id, filename, upload_timestamp
FROM JSON metadata
ORDER BY upload_timestamp DESC
LIMIT 10;
```

### 2. **Query Management Queries**
```sql
-- Get queries for a document
SELECT query_name, query_text, use_count, created_date
FROM saved_queries
WHERE doc_id = 'employees_20250906_114501'
ORDER BY use_count DESC;

-- Get popular queries
SELECT query_name, doc_id, use_count
FROM saved_queries
ORDER BY use_count DESC
LIMIT 10;

-- Get favorite queries
SELECT query_name, doc_id, description
FROM saved_queries
WHERE is_favorite = true;
```

### 3. **Report Management Queries**
```sql
-- Get reports for a document
SELECT report_name, format, generation_count, created_date
FROM saved_reports
WHERE doc_id = 'financial_data_20250901_114904'
ORDER BY generation_count DESC;

-- Get reports by format
SELECT report_name, doc_id, generation_count
FROM saved_reports
WHERE format = 'HTML'
ORDER BY generation_count DESC;
```

### 4. **Data Analysis Queries**
```sql
-- Get table statistics
SELECT 
    table_name,
    COUNT(*) as row_count,
    COUNT(DISTINCT column_name) as column_count
FROM information_schema.tables
WHERE table_schema = 'main'
GROUP BY table_name;

-- Get column information
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'main'
ORDER BY table_name, ordinal_position;
```

---

## Caching Strategies

### 1. **Query Result Caching**
```python
# Cache frequently used query results
def cache_query_result(query_hash: str, result: dict, ttl: int = 3600):
    cache_key = f"query:{query_hash}"
    redis_client.setex(cache_key, ttl, json.dumps(result))

def get_cached_query_result(query_hash: str) -> dict:
    cache_key = f"query:{query_hash}"
    cached = redis_client.get(cache_key)
    return json.loads(cached) if cached else None
```

### 2. **Metadata Caching**
```python
# Cache document metadata
def cache_document_metadata(doc_id: str, metadata: dict):
    cache_key = f"metadata:{doc_id}"
    redis_client.setex(cache_key, 86400, json.dumps(metadata))  # 24 hour TTL

def get_cached_metadata(doc_id: str) -> dict:
    cache_key = f"metadata:{doc_id}"
    cached = redis_client.get(cache_key)
    return json.loads(cached) if cached else None
```

### 3. **Agent Response Caching**
```python
# Cache agent responses for similar queries
def cache_agent_response(query_text: str, response: dict, ttl: int = 1800):
    query_hash = hashlib.md5(query_text.encode()).hexdigest()
    cache_key = f"agent:{query_hash}"
    redis_client.setex(cache_key, ttl, json.dumps(response))
```

---

## Data Privacy and Security

### 1. **Data Classification**
- **Public**: Document types, query patterns, report configurations
- **Internal**: User queries, report generations, usage statistics
- **Confidential**: Actual Excel data, user-specific information
- **Restricted**: System logs, error details, debugging information

### 2. **Access Control**
```python
# Role-based access control
class DataAccessControl:
    ROLES = {
        'admin': ['read', 'write', 'delete', 'manage'],
        'analyst': ['read', 'write'],
        'viewer': ['read']
    }
    
    def check_access(self, user_role: str, operation: str, resource: str) -> bool:
        if user_role not in self.ROLES:
            return False
        return operation in self.ROLES[user_role]
```

### 3. **Data Encryption**
- **At Rest**: DuckDB database files encrypted
- **In Transit**: HTTPS for all API communications
- **In Memory**: Sensitive data encrypted in memory
- **Backup**: Encrypted backups with key rotation

---

## Performance Optimization

### 1. **Database Indexing**
```sql
-- Create indexes for common queries
CREATE INDEX idx_saved_queries_doc_id ON saved_queries(doc_id);
CREATE INDEX idx_saved_queries_favorite ON saved_queries(is_favorite);
CREATE INDEX idx_saved_reports_doc_id ON saved_reports(doc_id);
CREATE INDEX idx_doc_registry_code ON doc_registry(document_type_code);
```

### 2. **Query Optimization**
```python
# Query optimization patterns
def optimize_query(sql: str) -> str:
    # Add LIMIT clauses for large datasets
    if 'LIMIT' not in sql.upper():
        sql += ' LIMIT 1000'
    
    # Use prepared statements for repeated queries
    return sql

# Connection pooling
def get_db_connection():
    return connection_pool.get_connection()
```

### 3. **Memory Management**
```python
# Efficient data processing
def process_large_dataset(file_path: str, chunk_size: int = 10000):
    for chunk in pd.read_excel(file_path, chunksize=chunk_size):
        yield process_chunk(chunk)

# Memory cleanup
def cleanup_memory():
    gc.collect()
    clear_agent_memory()
```

---

## LangChain Integration Patterns

### 1. **Database Tool Integration**
```python
from langchain.tools import BaseTool

class DatabaseQueryTool(BaseTool):
    name = "database_query"
    description = "Execute SQL queries on the DuckDB database"
    
    def _run(self, sql: str, doc_id: str) -> str:
        conn = get_db_connection()
        try:
            result = conn.execute(sql).fetchall()
            return json.dumps(result)
        finally:
            conn.close()
```

### 2. **Metadata Retrieval Tool**
```python
class MetadataRetrievalTool(BaseTool):
    name = "metadata_retrieval"
    description = "Retrieve document metadata and schema information"
    
    def _run(self, doc_id: str) -> str:
        metadata = load_metadata(doc_id)
        return json.dumps(metadata)
```

### 3. **Query History Tool**
```python
class QueryHistoryTool(BaseTool):
    name = "query_history"
    description = "Retrieve saved queries and reports for a document"
    
    def _run(self, doc_id: str, query_type: str = "all") -> str:
        if query_type == "queries":
            queries = get_saved_queries(doc_id)
            return json.dumps(queries)
        elif query_type == "reports":
            reports = get_saved_reports(doc_id)
            return json.dumps(reports)
        else:
            all_items = {
                "queries": get_saved_queries(doc_id),
                "reports": get_saved_reports(doc_id)
            }
            return json.dumps(all_items)
```

This comprehensive data architecture blueprint provides the foundation for LangChain agent integration and enables seamless AutoGen migration by documenting all data models, relationships, and access patterns in the Excel Reporting POC system.
