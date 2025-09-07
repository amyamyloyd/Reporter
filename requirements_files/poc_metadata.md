# POC Metadata Schema Documentation

## Overview

This document defines the complete metadata schema for the Excel Reporting POC, including database table structures, JSON file formats, and example implementations. All schemas are 100% accurate based on the current codebase implementation.

---

## Database Table Structures

### 1. doc_registry Table

**Purpose**: Stores document types and their field patterns for auto-classification and reuse detection.

```sql
CREATE TABLE IF NOT EXISTS doc_registry (
    id INTEGER PRIMARY KEY,
    document_type VARCHAR NOT NULL,                    -- Full document type name (e.g., "Employee Data")
    document_type_code VARCHAR NOT NULL,              -- Short code (e.g., "EMP")
    field_pattern VARCHAR NOT NULL,                   -- JSON array of field patterns for classification
    reuse_regularly BOOLEAN DEFAULT false,            -- Whether this document type is reused frequently
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When this pattern was first identified
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Last time pattern was updated
    description VARCHAR,                              -- Human-readable description
    example_filename VARCHAR,                         -- Example file that matches this pattern
    latest_version VARCHAR DEFAULT '1.0'              -- Current version of the pattern
);
```

**Example Data**:
```sql
INSERT INTO doc_registry VALUES 
(1, 'Employee Data', 'EMP', '["Employee ID", "Name", "Department", "Salary"]', true, '2025-01-01 10:00:00', '2025-01-01 10:00:00', 'Human resources employee records', 'employees_2025.xlsx', '1.0'),
(2, 'Hospital Asset Management', 'HAM', '["Account Number", "Entity", "Cost Center", "Asset Group"]', true, '2025-01-01 10:00:00', '2025-01-01 10:00:00', 'Hospital financial and asset tracking', 'HospitalA.xlsx', '1.0');
```

### 2. saved_queries Table

**Purpose**: Stores all saved queries with metadata for retrieval, reuse, and intelligent classification.

```sql
CREATE TABLE IF NOT EXISTS saved_queries (
    id INTEGER PRIMARY KEY,
    doc_id VARCHAR NOT NULL,                          -- Document identifier from upload
    document_type VARCHAR,                            -- Document type (e.g., "Employee Data")
    document_type_code VARCHAR,                       -- Document type code (e.g., "EMP")
    query_name VARCHAR NOT NULL,                      -- Human-readable query name
    query_text TEXT NOT NULL,                         -- Natural language query description
    sql TEXT NOT NULL,                                -- Actual SQL query
    sql_hash VARCHAR,                                 -- Hash of normalized SQL for uniqueness detection
    is_global BOOLEAN DEFAULT FALSE,                  -- True if saved globally, False if doc-specific only
    tags TEXT,                                        -- JSON array of tags for categorization
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When query was created
    last_used TIMESTAMP,                              -- Last time query was executed
    use_count INTEGER DEFAULT 0,                      -- Number of times query has been used
    description TEXT                                  -- Additional query description
);
```

**Example Data**:
```sql
INSERT INTO saved_queries VALUES 
(1, 'employees_20250101_100000', 'Employee Data', 'EMP', 'High Salary Employees', 'Find employees earning more than $100k', 'SELECT * FROM employees_20250101_100000 WHERE salary > 100000', 'abc123hash', true, '["salary", "filter", "high-earners"]', '2025-01-01 10:00:00', '2025-01-01 11:00:00', 5, 'Query for identifying high-earning employees'),
(2, 'HospitalA_20250906_194959', 'Hospital Asset Management', 'HAM', 'Cost Center 200 Records', 'list all records with cost center code of 200', 'SELECT * FROM "HospitalA_20250906_194959" WHERE LOWER("Cost Center Code") = ''200'' LIMIT 1000', 'def456hash', false, '["cost-center", "filter", "200"]', '2025-09-06 19:50:37', '2025-09-06 19:50:37', 1, 'Filter records by specific cost center');
```

### 3. saved_reports Table

**Purpose**: Stores all saved reports with configuration and metadata for retrieval and reuse.

```sql
CREATE TABLE IF NOT EXISTS saved_reports (
    id INTEGER PRIMARY KEY,
    doc_id VARCHAR NOT NULL,                          -- Document identifier from upload
    document_type VARCHAR,                            -- Document type (e.g., "Employee Data")
    document_type_code VARCHAR,                       -- Document type code (e.g., "EMP")
    report_name VARCHAR NOT NULL,                     -- Human-readable report name
    sql TEXT,                                         -- SQL used to generate report
    sql_hash VARCHAR,                                 -- Hash of normalized SQL for uniqueness detection
    is_global BOOLEAN DEFAULT FALSE,                  -- True if saved globally, False if doc-specific only
    filters TEXT,                                     -- JSON object of applied filters
    group_by TEXT,                                    -- JSON array of group by fields
    format VARCHAR,                                   -- Report format (table, chart, etc.)
    chart VARCHAR,                                    -- Chart type (bar, line, pie, etc.)
    output_type VARCHAR,                              -- Output format (html, xlsx, json)
    description TEXT,                                 -- Report description
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When report was created
    last_generated TIMESTAMP,                         -- Last time report was generated
    generation_count INTEGER DEFAULT 0                -- Number of times report has been generated
);
```

**Example Data**:
```sql
INSERT INTO saved_reports VALUES 
(1, 'employees_20250101_100000', 'Employee Data', 'EMP', 'Department Salary Summary', 'SELECT department, AVG(salary) as avg_salary, COUNT(*) as employee_count FROM employees_20250101_100000 GROUP BY department', 'ghi789hash', true, '{"min_salary": 50000}', '["department"]', 'chart', 'bar', 'xlsx', 'Salary analysis by department', '2025-01-01 10:00:00', '2025-01-01 11:00:00', 3),
(2, 'HospitalA_20250906_194959', 'Hospital Asset Management', 'HAM', 'Asset Cost Analysis', 'SELECT "Asset Group", SUM("Cost") as total_cost, COUNT(*) as asset_count FROM "HospitalA_20250906_194959" GROUP BY "Asset Group"', 'jkl012hash', false, '{"min_cost": 1000}', '["Asset Group"]', 'table', null, 'xlsx', 'Asset cost breakdown by group', '2025-09-06 19:50:37', '2025-09-06 19:50:37', 1);
```

---

## JSON File Schema

### Complete JSON File Structure

**File Location**: `backend/stored_queries/{filename}_{document_type_code}_{timestamp}.json`

**Purpose**: Comprehensive metadata file containing document information, sheet structures, queries, and reports for a single uploaded Excel file.

```json
{
  "filename": "employees_2025.xlsx",
  "json_filename": "employees_2025_emp_20250101_100000.json",
  "document_type": "Employee Data",
  "document_type_code": "emp",
  "data_version": "2025-01-01",
  "upload_timestamp": "2025-01-01_100000",
  "file_size": 245760,
  "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "sheets": {
    "Sheet1": {
      "fields": [
        "Employee ID",
        "First Name",
        "Last Name",
        "Department",
        "Position",
        "Salary",
        "Hire Date",
        "Manager ID"
      ],
      "normalized_fields": [
        "Employee_ID",
        "First_Name",
        "Last_Name",
        "Department",
        "Position",
        "Salary",
        "Hire_Date",
        "Manager_ID"
      ],
      "field_mapping": {
        "Employee ID": "Employee_ID",
        "First Name": "First_Name",
        "Last Name": "Last_Name",
        "Department": "Department",
        "Position": "Position",
        "Salary": "Salary",
        "Hire Date": "Hire_Date",
        "Manager ID": "Manager_ID"
      },
      "types": {
        "Employee_ID": "int64",
        "First_Name": "object",
        "Last_Name": "object",
        "Department": "object",
        "Position": "object",
        "Salary": "float64",
        "Hire_Date": "datetime64[ns]",
        "Manager_ID": "int64"
      },
      "row_count": 150
    }
  },
  "record_count": 150,
  "duckdb_table_name": "employees_2025_emp_20250101_100000",
  "duckdb_loaded": true,
  "is_current_version": true,
  "conversation_status": "completed",
  "ready_for_sql_agent": true,
  "queries": [
    {
      "query_name": "High Salary Employees",
      "query_text": "Find employees earning more than $100,000",
      "sql": "SELECT * FROM employees_2025_emp_20250101_100000 WHERE salary > 100000",
      "summary": "Found 25 employees with salary > $100k",
      "timestamp": "2025-01-01T10:30:00.000000",
      "auto_saved": true,
      "query_id": 1,
      "is_global": true,
      "tags": ["salary", "filter", "high-earners"],
      "use_count": 3
    },
    {
      "query_name": "Department Headcount",
      "query_text": "Count employees by department",
      "sql": "SELECT department, COUNT(*) as employee_count FROM employees_2025_emp_20250101_100000 GROUP BY department ORDER BY employee_count DESC",
      "summary": "Department breakdown with 8 departments",
      "timestamp": "2025-01-01T10:45:00.000000",
      "auto_saved": true,
      "query_id": 2,
      "is_global": true,
      "tags": ["department", "count", "group-by"],
      "use_count": 1
    },
    {
      "query_name": "Excel Export: high_salary_employees_20250101_103000.xlsx",
      "query_text": "Excel export generated",
      "sql": "Excel export",
      "summary": "Generated Excel file with 25 rows",
      "timestamp": "2025-01-01T10:30:00.000000",
      "auto_saved": true,
      "excel_export": {
        "filename": "high_salary_employees_20250101_103000.xlsx",
        "download_url": "/download-excel/high_salary_employees_20250101_103000.xlsx",
        "filepath": "stored_queries/excel_exports/high_salary_employees_20250101_103000.xlsx",
        "row_count": 25,
        "column_count": 8,
        "generated_at": "2025-01-01T10:30:00.000000Z",
        "file_size_bytes": 15680,
        "export_type": "query_results",
        "llm_generated": true,
        "document_type": "Employee Data",
        "document_type_code": "emp"
      }
    }
  ],
  "reports": [
    {
      "report_name": "Department Salary Summary",
      "sql": "SELECT department, AVG(salary) as avg_salary, MIN(salary) as min_salary, MAX(salary) as max_salary, COUNT(*) as employee_count FROM employees_2025_emp_20250101_100000 GROUP BY department ORDER BY avg_salary DESC",
      "filters": {
        "min_salary": 50000,
        "exclude_contractors": true
      },
      "group_by": ["department"],
      "format": "chart",
      "chart": "bar",
      "output_type": "xlsx",
      "description": "Salary analysis by department with statistics",
      "timestamp": "2025-01-01T11:00:00.000000",
      "auto_saved": true,
      "report_id": 1,
      "is_global": true,
      "generation_count": 2
    }
  ],
  "last_updated": "2025-01-01T11:00:00.000000"
}
```

---

## Field Definitions

### Core Document Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filename` | string | Yes | Original Excel filename |
| `json_filename` | string | Yes | Generated JSON metadata filename |
| `document_type` | string | Yes | Full document type name (e.g., "Employee Data") |
| `document_type_code` | string | Yes | Short lowercase code (e.g., "emp") |
| `data_version` | string | Yes | Version extracted from filename or current date |
| `upload_timestamp` | string | Yes | Upload timestamp in YYYYMMDD_HHMMSS format |
| `file_size` | integer | Yes | File size in bytes |
| `content_type` | string | Yes | MIME type of the uploaded file |
| `duckdb_table_name` | string | Yes | DuckDB table name for this data |
| `duckdb_loaded` | boolean | Yes | Whether data was successfully loaded to DuckDB |
| `is_current_version` | boolean | Yes | Whether this is the current version of this document type |
| `conversation_status` | string | Yes | Status of agent conversation ("completed", "pending", "failed") |
| `ready_for_sql_agent` | boolean | Yes | Whether data is ready for SQL agent processing |

### Sheet Structure Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sheets.{sheet_name}.fields` | array | Yes | Original field names from Excel |
| `sheets.{sheet_name}.normalized_fields` | array | Yes | Normalized field names (snake_case, SQL-safe) |
| `sheets.{sheet_name}.field_mapping` | object | Yes | Mapping between original and normalized field names |
| `sheets.{sheet_name}.types` | object | Yes | Pandas data types for each field |
| `sheets.{sheet_name}.row_count` | integer | Yes | Number of data rows in this sheet |

### Query Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query_name` | string | Yes | Human-readable query name |
| `query_text` | string | Yes | Natural language description of the query |
| `sql` | string | Yes | Actual SQL query |
| `summary` | string | Yes | Brief summary of query results |
| `timestamp` | string | Yes | ISO timestamp when query was created |
| `auto_saved` | boolean | Yes | Whether query was automatically saved |
| `query_id` | integer | No | Database ID if saved to saved_queries table |
| `is_global` | boolean | No | Whether query is available globally |
| `tags` | array | No | Tags for categorization |
| `use_count` | integer | No | Number of times query has been used |

### Excel Export Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filename` | string | Yes | Generated Excel filename |
| `download_url` | string | Yes | URL for downloading the file |
| `filepath` | string | Yes | Server file path |
| `row_count` | integer | Yes | Number of rows in exported file |
| `column_count` | integer | Yes | Number of columns in exported file |
| `generated_at` | string | Yes | ISO timestamp when file was generated |
| `file_size_bytes` | integer | Yes | Size of generated file in bytes |
| `export_type` | string | Yes | Type of export ("query_results", "report") |
| `llm_generated` | boolean | Yes | Whether file was generated by LLM |
| `document_type` | string | Yes | Document type of source data |
| `document_type_code` | string | Yes | Document type code of source data |

### Report Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `report_name` | string | Yes | Human-readable report name |
| `sql` | string | Yes | SQL query used to generate report |
| `filters` | object | No | Applied filters as key-value pairs |
| `group_by` | array | No | Fields used for grouping |
| `format` | string | Yes | Report format ("table", "chart") |
| `chart` | string | No | Chart type if applicable ("bar", "line", "pie") |
| `output_type` | string | Yes | Output format ("html", "xlsx", "json") |
| `description` | string | No | Report description |
| `timestamp` | string | Yes | ISO timestamp when report was created |
| `auto_saved` | boolean | Yes | Whether report was automatically saved |
| `report_id` | integer | No | Database ID if saved to saved_reports table |
| `is_global` | boolean | No | Whether report is available globally |
| `generation_count` | integer | No | Number of times report has been generated |

---

## Document Type Codes

| Document Type | Code | Description |
|---------------|------|-------------|
| Employee Data | emp | Human resources employee records |
| Hospital Asset Management | ham | Hospital financial and asset tracking |
| General Ledger | gl | Financial general ledger data |
| Campaign Data | campaign | Marketing campaign performance data |
| Vendor Reference | vendor | Vendor and supplier information |
| Inventory Data | inventory | Product inventory and stock levels |
| Sales Data | sales | Sales transactions and performance |
| Project Data | project | Project management and tracking |

---

## File Naming Conventions

### JSON Metadata Files
Format: `{original_filename}_{document_type_code}_{timestamp}.json`

Examples:
- `employees_2025_emp_20250101_100000.json`
- `HospitalA_ham_20250906_194959.json`
- `sales_q4_2024_sales_20250101_143000.json`

### DuckDB Table Names
Format: `{original_filename}_{document_type_code}_{timestamp}`

Examples:
- `employees_2025_emp_20250101_100000`
- `HospitalA_ham_20250906_194959`
- `sales_q4_2024_sales_20250101_143000`

### Excel Export Files
Format: `{query_name}_{timestamp}_{date}.xlsx`

Examples:
- `high_salary_employees_20250101_103000_202501.xlsx`
- `costcenter_200_records_20250906_194959_202509.xlsx`

---

## Data Type Mappings

### Pandas to SQL Type Mappings

| Pandas Type | SQL Type | Description |
|-------------|----------|-------------|
| `int64` | INTEGER | 64-bit integer |
| `float64` | DOUBLE | 64-bit floating point |
| `object` | VARCHAR | String/text data |
| `datetime64[ns]` | TIMESTAMP | Date and time |
| `bool` | BOOLEAN | True/false values |

### Field Normalization Rules

1. **Spaces to Underscores**: "First Name" → "First_Name"
2. **Special Characters Removed**: "Cost Center Code" → "Cost_Center_Code"
3. **Lowercase Conversion**: "EMPLOYEE_ID" → "employee_id"
4. **SQL Keywords Avoided**: "Order" → "order_field"
5. **Length Limitation**: Truncated to 64 characters maximum
6. **Uniqueness**: Duplicate names get numeric suffixes

---

## Validation Rules

### Required Fields Validation
- All core document fields must be present
- At least one sheet must exist in `sheets` object
- Each sheet must have all required structure fields
- Query objects must have all required fields if present
- Excel export objects must have all required fields if present

### Data Type Validation
- `file_size` must be positive integer
- `record_count` must be non-negative integer
- `is_current_version` must be boolean
- `duckdb_loaded` must be boolean
- `ready_for_sql_agent` must be boolean
- Timestamps must be valid ISO format strings

### Business Logic Validation
- Only one file per document type can have `is_current_version: true`
- `document_type_code` must match predefined codes
- `duckdb_table_name` must be SQL-safe
- Query SQL must be valid SQL syntax
- Excel export filenames must be unique

---

## Local Storage

### Overview

The frontend application uses browser localStorage to persist user session data and provide continuity across page refreshes. This section details all data stored in localStorage and its structure.

### Stored Data Structures

#### 1. recentUploads

**Purpose**: Maintains a list of recently uploaded files for quick access and session continuity.

**Storage Key**: `recentUploads`

**Data Structure**:
```json
[
  {
    "filename": "employees_2025.xlsx",
    "json_filename": "employees_2025_emp_20250101_100000.json",
    "document_type": "Employee Data",
    "document_type_code": "emp",
    "data_version": "2025-01-01",
    "upload_timestamp": "2025-01-01_100000",
    "file_size": 245760,
    "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "duckdb_table_name": "employees_2025_emp_20250101_100000",
    "duckdb_loaded": true,
    "is_current_version": true,
    "conversation_status": "completed",
    "ready_for_sql_agent": true,
    "uploadTimestamp": "2025-01-01T10:00:00.000Z",
    "uploadDate": "1/1/2025",
    "uploadTime": "10:00:00 AM",
    "fields": [
      "Employee ID",
      "First Name",
      "Last Name",
      "Department",
      "Position",
      "Salary",
      "Hire Date",
      "Manager ID"
    ],
    "record_count": 150
  }
]
```

**Field Descriptions**:

| Field | Type | Description |
|-------|------|-------------|
| `filename` | string | Original Excel filename |
| `json_filename` | string | Generated JSON metadata filename |
| `document_type` | string | Full document type name |
| `document_type_code` | string | Short document type code |
| `data_version` | string | Version extracted from filename |
| `upload_timestamp` | string | Upload timestamp in YYYYMMDD_HHMMSS format |
| `file_size` | integer | File size in bytes |
| `content_type` | string | MIME type of uploaded file |
| `duckdb_table_name` | string | DuckDB table name for this data |
| `duckdb_loaded` | boolean | Whether data was loaded to DuckDB |
| `is_current_version` | boolean | Whether this is current version of document type |
| `conversation_status` | string | Status of agent conversation |
| `ready_for_sql_agent` | boolean | Whether ready for SQL agent processing |
| `uploadTimestamp` | string | ISO timestamp when uploaded (added by frontend) |
| `uploadDate` | string | Human-readable upload date (added by frontend) |
| `uploadTime` | string | Human-readable upload time (added by frontend) |
| `fields` | array | Array of field names from the Excel file |
| `record_count` | integer | Number of data rows |

**Management Rules**:
- Maximum 20 recent uploads stored (prevents localStorage bloat)
- New uploads added to beginning of array (most recent first)
- Duplicates removed based on `json_filename` uniqueness
- Automatically cleared on upload failures
- Persists across browser sessions

#### 2. localStorageContext (Temporary)

**Purpose**: Context data passed to AutoGen agents for conversation continuity.

**Storage**: Temporary object created during agent conversations, not persistently stored.

**Data Structure**:
```json
{
  "doc_id": "employees_2025_emp_20250101_100000",
  "schema": [
    "Employee ID",
    "First Name",
    "Last Name",
    "Department",
    "Position",
    "Salary",
    "Hire Date",
    "Manager ID"
  ],
  "record_count": 150,
  "duckdb_table_name": "employees_2025_emp_20250101_100000",
  "metadata": {
    "document_type": "Employee Data",
    "document_type_code": "emp",
    "is_current_version": true
  },
  "recentUploads": [
    {
      "filename": "employees_2025.xlsx",
      "json_filename": "employees_2025_emp_20250101_100000.json",
      "doc_type": "Employee Data",
      "fields": ["Employee ID", "First Name", "Last Name"],
      "upload_time": "2025-01-01T10:00:00.000Z"
    }
  ]
}
```

**Field Descriptions**:

| Field | Type | Description |
|-------|------|-------------|
| `doc_id` | string | Document identifier for current conversation |
| `schema` | array | Field names available for querying |
| `record_count` | integer | Number of records in current document |
| `duckdb_table_name` | string | DuckDB table name for SQL queries |
| `metadata` | object | Additional document metadata |
| `recentUploads` | array | Simplified recent uploads for agent context |

### Local Storage Utility Functions

#### getRecentUploads()
```javascript
/**
 * Retrieve recent uploads from localStorage
 * @returns {Array} Array of recent upload objects
 */
export const getRecentUploads = () => {
  try {
    const recentUploads = localStorage.getItem('recentUploads');
    return recentUploads ? JSON.parse(recentUploads) : [];
  } catch (error) {
    console.warn('Failed to retrieve recent uploads from localStorage:', error);
    return [];
  }
};
```

#### clearRecentUploads()
```javascript
/**
 * Clear all recent uploads from localStorage
 */
export const clearRecentUploads = () => {
  try {
    localStorage.removeItem('recentUploads');
    console.log('✅ Cleared recent uploads from localStorage');
  } catch (error) {
    console.warn('Failed to clear recent uploads from localStorage:', error);
  }
};
```

### Data Flow

#### Upload Process
1. **File Upload**: User uploads Excel files via FileUploader
2. **API Response**: Backend returns complete file metadata
3. **localStorage Update**: Frontend adds upload metadata to `recentUploads`
4. **Deduplication**: Removes duplicates based on `json_filename`
5. **Size Management**: Keeps only 20 most recent uploads

#### Agent Conversation Process
1. **Context Creation**: AutoGenChat creates `localStorageContext` from current files
2. **Agent Communication**: Context sent to backend for agent processing
3. **Session Continuity**: Agents can reference recent uploads and current schema

#### Session Management
1. **Page Refresh**: `recentUploads` persists across browser sessions
2. **New Session**: User can continue with previously uploaded files
3. **Error Handling**: localStorage failures don't break core functionality

### Storage Limits and Considerations

#### Browser Limits
- **Chrome/Edge**: ~10MB per origin
- **Firefox**: ~10MB per origin
- **Safari**: ~5MB per origin

#### Current Usage
- **Per Upload**: ~2-5KB (depending on field count)
- **20 Uploads**: ~40-100KB total
- **Well Within Limits**: Current usage is minimal

#### Error Handling
- **JSON Parse Errors**: Graceful fallback to empty array
- **Storage Quota Exceeded**: Logs warning, continues operation
- **Corrupted Data**: Clears and resets localStorage

### Security Considerations

#### Data Sensitivity
- **No Sensitive Data**: Only metadata stored, no actual Excel data
- **Public Information**: Filenames and field names are not sensitive
- **No Authentication**: localStorage is not secure storage

#### Best Practices
- **Validation**: All data validated before storage
- **Sanitization**: No user input directly stored
- **Error Boundaries**: localStorage failures don't crash application

---

## API Integration Points

### Upload Endpoint
- Creates JSON metadata file
- Updates `is_current_version` flags
- Loads data to DuckDB
- Returns complete metadata structure

### Query Endpoint
- Executes SQL queries
- Auto-saves queries to JSON and database
- Generates query summaries
- Updates use counts

### Report Endpoint
- Generates reports from queries
- Auto-saves reports to JSON and database
- Creates Excel exports
- Updates generation counts

### Download Endpoint
- Serves generated Excel files
- Tracks download statistics
- Validates file existence and permissions

---

This schema documentation is 100% accurate based on the current codebase implementation and provides the complete specification for the Excel Reporting POC metadata system.
