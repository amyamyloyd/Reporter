# Query and Report Endpoints Documentation

## Overview

This document provides comprehensive documentation for all API endpoints that can execute queries or generate reports in the Excel Reporting POC. All endpoints are RESTful and return JSON responses unless otherwise specified.

---

## Query Endpoints

### 1. Execute Query (Natural Language to SQL)

**Endpoint**: `POST /query`

**Purpose**: Converts natural language queries to SQL and executes them against DuckDB tables.

**Input Format**:
```json
{
    "doc_id": "hospital_ledger_fy2024_001",
    "query_text": "How much did we spend on Vendor X in Q2?",
    "schema": ["Vendor", "Date", "Amount"],
    "metadata": {"record_count": 1200, "created": "2024-01-01"},
    "datetime_context": {"now": "2025-09-02", "current_quarter": "Q3", "last_quarter": "Q2"}
}
```

**Input Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `doc_id` | string | Yes | Document identifier for the data source |
| `query_text` | string | Yes | Natural language query description |
| `schema` | array | Yes | Available field names for the query |
| `metadata` | object | Yes | Document metadata including record count |
| `datetime_context` | object | No | Context for date-related queries |

**Output Format**:
```json
{
    "success": true,
    "sql": "SELECT SUM(Amount) FROM hospital_ledger_fy2024_001 WHERE Vendor = 'Vendor X' AND Quarter = 'Q2'",
    "rows": [[124000.50]],
    "columns": ["Total Amount"],
    "summary": "We spent $124,000.50 on Vendor X in Q2.",
    "row_count": 1,
    "execution_time_ms": 45,
    "doc_id": "hospital_ledger_fy2024_001"
}
```

**Output Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether query executed successfully |
| `sql` | string | Generated SQL query |
| `rows` | array | Query result rows |
| `columns` | array | Column names for results |
| `summary` | string | Human-readable summary of results |
| `row_count` | integer | Number of rows returned |
| `execution_time_ms` | integer | Query execution time in milliseconds |
| `doc_id` | string | Document ID that was queried |

---

### 2. Execute Saved Query by Name

**Endpoint**: `GET /execute_query/{query_name}`

**Purpose**: Executes a previously saved query by its name.

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query_name` | string | Yes | Name of the saved query to execute |

**Example**: `GET /execute_query/Quarterly%20Vendor%20Spend`

**Output Format**:
```json
{
    "success": true,
    "query_name": "Quarterly Vendor Spend",
    "query_id": 123,
    "doc_id": "hospital_ledger_fy2024_001",
    "sql": "SELECT Quarter, SUM(Amount) FROM hospital_ledger_fy2024_001 GROUP BY Quarter",
    "rows": [["Q1", 450000.00], ["Q2", 520000.00], ["Q3", 480000.00]],
    "columns": ["Quarter", "Total Amount"],
    "summary": "Quarterly spending: Q1 $450K, Q2 $520K, Q3 $480K",
    "row_count": 3,
    "execution_time_ms": 67,
    "use_count": 5,
    "last_used": "2025-01-01T10:30:00.000Z"
}
```

**Output Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether query executed successfully |
| `query_name` | string | Name of the executed query |
| `query_id` | integer | Database ID of the query |
| `doc_id` | string | Document ID that was queried |
| `sql` | string | SQL query that was executed |
| `rows` | array | Query result rows |
| `columns` | array | Column names for results |
| `summary` | string | Human-readable summary of results |
| `row_count` | integer | Number of rows returned |
| `execution_time_ms` | integer | Query execution time in milliseconds |
| `use_count` | integer | Number of times this query has been used |
| `last_used` | string | ISO timestamp of last execution |

---

### 3. Save Query

**Endpoint**: `POST /save_query`

**Purpose**: Saves a query to both DuckDB and document metadata JSON.

**Input Format**:
```json
{
    "doc_id": "hospital_ledger_fy2024_001",
    "query_text": "How much did we spend on Vendor X in Q2?",
    "sql": "SELECT SUM(Amount) FROM hospital_ledger_fy2024_001 WHERE Vendor = 'Vendor X' AND Quarter = 'Q2'",
    "query_name": "Quarterly Vendor Spend",
    "tags": ["vendor", "q2", "spending"]
}
```

**Input Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `doc_id` | string | Yes | Document identifier |
| `query_text` | string | Yes | Natural language description |
| `sql` | string | Yes | SQL query to save |
| `query_name` | string | Yes | Human-readable name for the query |
| `tags` | array | No | Tags for categorization |

**Output Format**:
```json
{
    "success": true,
    "message": "Query 'Quarterly Vendor Spend' saved successfully",
    "doc_id": "hospital_ledger_fy2024_001",
    "query_name": "Quarterly Vendor Spend",
    "query_text": "How much did we spend on Vendor X in Q2?",
    "sql": "SELECT SUM(Amount) FROM hospital_ledger_fy2024_001 WHERE Vendor = 'Vendor X' AND Quarter = 'Q2'",
    "tags": ["vendor", "q2", "spending"],
    "saved_to_db": true,
    "saved_to_metadata": true,
    "timestamp": "2025-01-01T10:30:00.000Z"
}
```

---

### 4. Get Saved Queries

**Endpoint**: `GET /saved_queries`

**Purpose**: Retrieves saved queries for navigation and management.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `doc_id` | string | No | Single document ID |
| `doc_ids` | string | No | Comma-separated list of document IDs |

**Examples**:
- `GET /saved_queries?doc_id=hospital_ledger_fy2024_001`
- `GET /saved_queries?doc_ids=doc1,doc2,doc3`

**Output Format**:
```json
{
    "success": true,
    "message": "Retrieved 5 saved queries",
    "doc_ids": ["hospital_ledger_fy2024_001"],
    "queries": [
        {
            "id": 123,
            "doc_id": "hospital_ledger_fy2024_001",
            "query_name": "Quarterly Vendor Spend",
            "query_text": "How much did we spend on Vendor X in Q2?",
            "sql": "SELECT SUM(Amount) FROM hospital_ledger_fy2024_001 WHERE Vendor = 'Vendor X' AND Quarter = 'Q2'",
            "tags": ["vendor", "q2", "spending"],
            "created_date": "2025-01-01T10:00:00.000Z",
            "last_used": "2025-01-01T10:30:00.000Z",
            "use_count": 5,
            "description": "Saved query: Quarterly Vendor Spend"
        }
    ],
    "count": 5
}
```

---

## Report Endpoints

### 1. Generate Report

**Endpoint**: `POST /report`

**Purpose**: Generates reports with filters, grouping, and formatting.

**Input Format**:
```json
{
    "doc_id": "hospital_ledger_fy2024_001",
    "report_name": "Weekly Vendor Spend",
    "sql": "SELECT Week, SUM(Amount) FROM hospital_ledger_fy2024_001 GROUP BY Week",
    "filters": {"vendor": "Vendor X", "quarter": "Q2"},
    "group_by": ["Week"],
    "format": "chart",
    "chart": "bar",
    "output_type": "html"
}
```

**Input Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `doc_id` | string | Yes | Document identifier |
| `report_name` | string | Yes | Name for the report |
| `sql` | string | Yes | SQL query to execute |
| `filters` | object | No | Applied filters as key-value pairs |
| `group_by` | array | No | Fields to group by |
| `format` | string | No | Report format ("table", "chart") |
| `chart` | string | No | Chart type ("bar", "line", "pie") |
| `output_type` | string | No | Output format ("html", "xlsx", "json") |

**Output Format** (HTML):
```json
{
    "success": true,
    "report_name": "Weekly Vendor Spend",
    "output_type": "html",
    "html_content": "<table><tr><th>Week</th><th>Total Amount</th></tr><tr><td>Week 1</td><td>$50,000</td></tr></table>",
    "row_count": 4,
    "columns": ["Week", "Total Amount"],
    "filters_applied": {"vendor": "Vendor X", "quarter": "Q2"},
    "group_by": ["Week"],
    "format": "chart",
    "chart": "bar",
    "execution_time_ms": 89
}
```

**Output Format** (XLSX):
```json
{
    "success": true,
    "report_name": "Weekly Vendor Spend",
    "output_type": "xlsx",
    "download_url": "/download-excel/weekly_vendor_spend_20250101_103000.xlsx",
    "filename": "weekly_vendor_spend_20250101_103000.xlsx",
    "filepath": "stored_queries/excel_exports/weekly_vendor_spend_20250101_103000.xlsx",
    "row_count": 4,
    "column_count": 2,
    "file_size_bytes": 15680,
    "generated_at": "2025-01-01T10:30:00.000Z"
}
```

---

### 2. Execute Saved Report by Name

**Endpoint**: `GET /execute_report/{report_name}`

**Purpose**: Executes a previously saved report by its name.

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `report_name` | string | Yes | Name of the saved report to execute |

**Example**: `GET /execute_report/Weekly%20Vendor%20Spend`

**Output Format**: Same as `/report` endpoint based on the saved report's configuration.

---

### 3. Save Report

**Endpoint**: `POST /save_report`

**Purpose**: Saves a report configuration to both DuckDB and document metadata JSON.

**Input Format**:
```json
{
    "doc_id": "hospital_ledger_fy2024_001",
    "report_name": "Weekly Vendor Spend",
    "sql": "SELECT Week, SUM(Amount) FROM hospital_ledger_fy2024_001 GROUP BY Week",
    "filters": {"vendor": "Vendor X", "quarter": "Q2"},
    "group_by": ["Week"],
    "format": "chart",
    "chart": "bar",
    "description": "Summarizes weekly spending by vendor."
}
```

**Input Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `doc_id` | string | Yes | Document identifier |
| `report_name` | string | Yes | Human-readable name for the report |
| `sql` | string | No | SQL query for the report |
| `filters` | object | No | Applied filters |
| `group_by` | array | No | Grouping fields |
| `format` | string | No | Report format |
| `chart` | string | No | Chart type |
| `description` | string | No | Report description |

**Output Format**:
```json
{
    "success": true,
    "message": "Report 'Weekly Vendor Spend' saved successfully",
    "doc_id": "hospital_ledger_fy2024_001",
    "report_name": "Weekly Vendor Spend",
    "sql": "SELECT Week, SUM(Amount) FROM hospital_ledger_fy2024_001 GROUP BY Week",
    "filters": {"vendor": "Vendor X", "quarter": "Q2"},
    "group_by": ["Week"],
    "format": "chart",
    "chart": "bar",
    "description": "Summarizes weekly spending by vendor.",
    "saved_to_db": true,
    "saved_to_metadata": true,
    "timestamp": "2025-01-01T10:30:00.000Z"
}
```

---

### 4. Get Saved Reports

**Endpoint**: `GET /saved_reports`

**Purpose**: Retrieves saved reports for navigation and management.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `doc_id` | string | No | Single document ID |
| `doc_ids` | string | No | Comma-separated list of document IDs |

**Examples**:
- `GET /saved_reports?doc_id=hospital_ledger_fy2024_001`
- `GET /saved_reports?doc_ids=doc1,doc2,doc3`

**Output Format**:
```json
{
    "success": true,
    "message": "Retrieved 3 saved reports",
    "doc_ids": ["hospital_ledger_fy2024_001"],
    "reports": [
        {
            "id": 456,
            "doc_id": "hospital_ledger_fy2024_001",
            "report_name": "Weekly Vendor Spend",
            "sql": "SELECT Week, SUM(Amount) FROM hospital_ledger_fy2024_001 GROUP BY Week",
            "filters": {"vendor": "Vendor X", "quarter": "Q2"},
            "group_by": ["Week"],
            "format": "chart",
            "chart": "bar",
            "output_type": "html",
            "description": "Summarizes weekly spending by vendor.",
            "created_date": "2025-01-01T10:00:00.000Z",
            "last_generated": "2025-01-01T10:30:00.000Z",
            "generation_count": 3
        }
    ],
    "count": 3
}
```

---

## File Management Endpoints

### 1. Download Excel File

**Endpoint**: `GET /download-excel/{filename}`

**Purpose**: Downloads generated Excel files.

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filename` | string | Yes | Excel filename to download |

**Example**: `GET /download-excel/weekly_vendor_spend_20250101_103000.xlsx`

**Output**: Binary Excel file download

**Response Headers**:
- `Content-Type`: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition`: `attachment; filename="filename.xlsx"`

---

### 2. List JSON Files

**Endpoint**: `GET /list-json-files`

**Purpose**: Lists all available JSON metadata files.

**Output Format**:
```json
{
    "success": true,
    "files": [
        "hospital_ledger_fy2024_001.json",
        "employee_data_20250101_100000.json",
        "inventory_q4_2024.json"
    ],
    "count": 3,
    "message": "Found 3 JSON files"
}
```

---

## Utility Endpoints

### 1. Check Tables

**Endpoint**: `GET /check-tables`

**Purpose**: Lists all tables in DuckDB and their structure.

**Output Format**:
```json
{
    "success": true,
    "tables": [
        {
            "name": "hospital_ledger_fy2024_001",
            "columns": [
                {"name": "Vendor", "type": "VARCHAR"},
                {"name": "Date", "type": "DATE"},
                {"name": "Amount", "type": "DOUBLE"}
            ],
            "row_count": 1200
        }
    ],
    "count": 1
}
```

---

### 2. Get Document Registry

**Endpoint**: `GET /doc-registry`

**Purpose**: Retrieves document type registry for classification.

**Output Format**:
```json
{
    "success": true,
    "registry": [
        {
            "id": 1,
            "document_type": "Hospital Asset Management",
            "document_type_code": "HAM",
            "field_pattern": "[\"Account Number\", \"Entity\", \"Cost Center\"]",
            "reuse_regularly": true,
            "created_date": "2025-01-01T10:00:00.000Z",
            "updated_date": "2025-01-01T10:00:00.000Z",
            "description": "Hospital financial and asset tracking",
            "example_filename": "HospitalA.xlsx",
            "latest_version": "1.0"
        }
    ],
    "count": 1
}
```

---

## Error Handling

### Standard Error Response Format

All endpoints return errors in this format:

```json
{
    "detail": "Error message describing what went wrong",
    "status_code": 400
}
```

### Common HTTP Status Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| 400 | Bad Request | Missing required fields, invalid input format |
| 404 | Not Found | Query/report not found, file not found |
| 500 | Internal Server Error | Database errors, file processing errors |

### Error Examples

**Missing Required Field**:
```json
{
    "detail": "Missing required field: doc_id",
    "status_code": 400
}
```

**Query Not Found**:
```json
{
    "detail": "Query with name 'NonExistentQuery' not found",
    "status_code": 404
}
```

**File Not Found**:
```json
{
    "detail": "File not found",
    "status_code": 404
}
```

---

## Usage Examples

### Complete Query Workflow

1. **Execute Query**:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "hospital_ledger_fy2024_001",
    "query_text": "Show me total spending by vendor",
    "schema": ["Vendor", "Amount"],
    "metadata": {"record_count": 1200}
  }'
```

2. **Save Query**:
```bash
curl -X POST "http://localhost:8000/save_query" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "hospital_ledger_fy2024_001",
    "query_text": "Show me total spending by vendor",
    "sql": "SELECT Vendor, SUM(Amount) FROM hospital_ledger_fy2024_001 GROUP BY Vendor",
    "query_name": "Vendor Spending Summary",
    "tags": ["vendor", "spending", "summary"]
  }'
```

3. **Execute Saved Query**:
```bash
curl -X GET "http://localhost:8000/execute_query/Vendor%20Spending%20Summary"
```

### Complete Report Workflow

1. **Generate Report**:
```bash
curl -X POST "http://localhost:8000/report" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "hospital_ledger_fy2024_001",
    "report_name": "Monthly Spending Trends",
    "sql": "SELECT Month, SUM(Amount) FROM hospital_ledger_fy2024_001 GROUP BY Month",
    "format": "chart",
    "chart": "line",
    "output_type": "xlsx"
  }'
```

2. **Download Generated File**:
```bash
curl -X GET "http://localhost:8000/download-excel/monthly_spending_trends_20250101_103000.xlsx" \
  --output report.xlsx
```

---

This documentation covers all available query and report endpoints in the Excel Reporting POC system. Each endpoint includes detailed input/output specifications, error handling, and usage examples for complete integration guidance.
