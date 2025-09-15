# API Endpoint Registry - Excel Reporting POC

## Overview
Complete catalog of all REST endpoints for LangChain tool generation and AutoGen integration. This documentation provides OpenAPI 3.0 compliant schemas and comprehensive business context for AI agent orchestration.

**Base URL**: `http://localhost:8000` (development)  
**Authentication**: None required for POC  
**Content-Type**: `application/json` (except file uploads)

---

## Core System Endpoints

### GET /
**Purpose**: Root endpoint for API health verification  
**Business Context**: Entry point for system availability checks

**Response Schema**:
```json
{
  "message": "AI Excel Reporting API is running"
}
```

**Status Codes**:
- `200`: API is running successfully

**Example**:
```bash
curl -X GET http://localhost:8000/
```

---

### GET /health
**Purpose**: System health check with environment information  
**Business Context**: Monitoring and diagnostics endpoint

**Response Schema**:
```json
{
  "status": "healthy",
  "environment": "development"
}
```

**Status Codes**:
- `200`: System is healthy

**Example**:
```bash
curl -X GET http://localhost:8000/health
```

---

## File Management Endpoints

### POST /upload
**Purpose**: Upload and process Excel files for analysis  
**Business Context**: Entry point for file analysis workflow

**Request Schema**:
```json
{
  "files": [
    {
      "filename": "string",
      "content": "multipart/form-data"
    }
  ]
}
```

**Response Schema**:
```json
{
  "success": true,
  "files": [
    {
      "filename": "string",
      "json_filename": "string",
      "metadata": {
        "sheets": {
          "Sheet1": {
            "fields": ["string"],
            "types": {"field": "string"},
            "row_count": 0
          }
        },
        "total_sheets": 0,
        "total_fields": 0,
        "total_rows": 0
      },
      "excel_path": "string",
      "json_path": "string"
    }
  ],
  "session_id": "string",
  "message": "string"
}
```

**Error Responses**:
- `400`: Validation errors (file format, size limits)
- `500`: Processing errors

**Validation Rules**:
- Maximum 5 files per request
- Maximum 50MB per file
- Only `.xlsx` and `.xls` formats accepted
- Files must contain valid Excel data

**Dependencies**: None  
**Rate Limiting**: 5 files per request  
**Idempotency**: Not idempotent - creates new analysis session

**Example**:
```bash
curl -X POST http://localhost:8000/upload \
  -F "files=@data.xlsx" \
  -F "files=@report.xlsx"
```

---

### GET /download-excel/{filename}
**Purpose**: Download generated Excel files  
**Business Context**: Retrieve processed Excel outputs

**Path Parameters**:
- `filename` (string): Name of the file to download

**Response**: Excel file download

**Status Codes**:
- `200`: File downloaded successfully
- `404`: File not found
- `500`: Download error

**Example**:
```bash
curl -X GET http://localhost:8000/download-excel/report_2024.xlsx \
  --output report.xlsx
```

---

## Agent System Endpoints

### POST /autogen-chat
**Purpose**: Main AutoGen agent conversation endpoint  
**Business Context**: Primary entry point for AI agent interactions

**Request Schema**:
```json
{
  "user_input": "string",
  "localStorage_context": {
    "session_id": "string",
    "uploaded_files": ["string"],
    "current_doc_id": "string"
  }
}
```

**Response Schema**:
```json
{
  "success": true,
  "agent_response": "string",
  "routing_info": {
    "target_agent": "string",
    "conversation_id": "string"
  },
  "results": {
    "query_results": {},
    "report_results": {},
    "file_analysis": {}
  },
  "next_actions": ["string"],
  "error": "string"
}
```

**Error Responses**:
- `400`: Missing user_input
- `500`: Agent conversation failed

**Dependencies**: Requires uploaded files for analysis  
**Rate Limiting**: None  
**Idempotency**: Not idempotent - creates conversation state

**Example**:
```bash
curl -X POST http://localhost:8000/autogen-chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Analyze the sales data and show me top performers",
    "localStorage_context": {
      "session_id": "session_123",
      "uploaded_files": ["sales_data.xlsx"]
    }
  }'
```

---

### GET /autogen-status
**Purpose**: Get status of all AutoGen agents  
**Business Context**: System monitoring and diagnostics

**Response Schema**:
```json
{
  "status": "healthy",
  "agents": {
    "ChatAgent": "active",
    "OrchestrationAgent": "active",
    "QueryAgent": "active",
    "ReportAgent": "active",
    "UploadAgent": "active",
    "MemoryAgent": "active"
  },
  "active_conversations": 0,
  "last_activity": "2024-01-01T00:00:00Z"
}
```

**Status Codes**:
- `200`: Status retrieved successfully

**Example**:
```bash
curl -X GET http://localhost:8000/autogen-status
```

---

### POST /chat-agent
**Purpose**: Progressive ChatAgent conversation for user input collection  
**Business Context**: Step-by-step user interaction for complex workflows

**Request Schema**:
```json
{
  "json_filename": "string",
  "user_response": "string",
  "conversation_step": "string",
  "session_id": "string"
}
```

**Response Schema**:
```json
{
  "success": true,
  "agent_message": "string",
  "conversation_step": "string",
  "next_question": "string",
  "is_complete": false,
  "collected_data": {},
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid conversation step
- `500`: Agent conversation failed

**Dependencies**: Requires valid session_id  
**Rate Limiting**: None  
**Idempotency**: Not idempotent - updates conversation state

---

## Query System Endpoints

### POST /query
**Purpose**: Natural language to SQL with DuckDB execution  
**Business Context**: Core query processing for data analysis

**Request Schema**:
```json
{
  "doc_id": "string",
  "query_text": "string",
  "schema": ["string"],
  "metadata": {
    "record_count": 0,
    "created": "string"
  },
  "datetime_context": {
    "now": "string",
    "current_quarter": "string",
    "last_quarter": "string"
  }
}
```

**Response Schema**:
```json
{
  "success": true,
  "sql": "string",
  "rows": [[]],
  "columns": ["string"],
  "summary": "string",
  "execution_time": 0.0,
  "row_count": 0,
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid query parameters
- `500`: SQL execution error

**Dependencies**: Requires valid doc_id with uploaded data  
**Rate Limiting**: None  
**Idempotency**: Idempotent - same query produces same results

**Example**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "hospital_ledger_fy2024_001",
    "query_text": "How much did we spend on Vendor X in Q2?",
    "schema": ["Vendor", "Date", "Amount"],
    "metadata": {"record_count": 1200, "created": "2024-01-01"},
    "datetime_context": {"now": "2025-09-02", "current_quarter": "Q3", "last_quarter": "Q2"}
  }'
```

---

### POST /save_query
**Purpose**: Persist queries to DuckDB and JSON metadata  
**Business Context**: Save successful queries for reuse and navigation

**Request Schema**:
```json
{
  "doc_id": "string",
  "query_name": "string",
  "query_text": "string",
  "sql": "string",
  "description": "string",
  "is_favorite": false
}
```

**Response Schema**:
```json
{
  "success": true,
  "query_id": 0,
  "message": "string",
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid query data
- `500`: Database save error

**Dependencies**: Requires valid doc_id  
**Rate Limiting**: None  
**Idempotency**: Not idempotent - creates new query record

---

### GET /saved_queries
**Purpose**: Retrieve saved queries for navigation  
**Business Context**: Frontend navigation and query management

**Query Parameters**:
- `doc_id` (optional): Filter by document ID
- `doc_ids` (optional): Comma-separated list of document IDs

**Response Schema**:
```json
{
  "success": true,
  "queries": [
    {
      "id": 0,
      "doc_id": "string",
      "query_name": "string",
      "query_text": "string",
      "sql": "string",
      "description": "string",
      "is_favorite": false,
      "created_at": "string"
    }
  ],
  "error": "string"
}
```

**Status Codes**:
- `200`: Queries retrieved successfully
- `500`: Database error

**Example**:
```bash
curl -X GET "http://localhost:8000/saved_queries?doc_id=hospital_ledger_fy2024_001"
```

---

### GET /execute_query/{query_name}
**Purpose**: Execute saved query by name  
**Business Context**: Click-to-run functionality for saved queries

**Path Parameters**:
- `query_name` (string): Name of the saved query to execute

**Response Schema**:
```json
{
  "success": true,
  "query_name": "string",
  "sql": "string",
  "rows": [[]],
  "columns": ["string"],
  "execution_time": 0.0,
  "row_count": 0,
  "error": "string"
}
```

**Error Responses**:
- `404`: Query not found
- `500`: Execution error

**Dependencies**: Requires saved query with valid SQL  
**Rate Limiting**: None  
**Idempotency**: Idempotent - same query produces same results

---

## Report System Endpoints

### POST /report
**Purpose**: Generate reports with filters, grouping, and formatting  
**Business Context**: Advanced reporting with natural language titles

**Request Schema**:
```json
{
  "doc_id": "string",
  "report_name": "string",
  "filters": {
    "field": "value"
  },
  "group_by": ["string"],
  "aggregations": {
    "field": "sum|avg|count|min|max"
  },
  "sort_by": "string",
  "sort_order": "asc|desc",
  "limit": 0
}
```

**Response Schema**:
```json
{
  "success": true,
  "report_name": "string",
  "sql": "string",
  "rows": [[]],
  "columns": ["string"],
  "summary": "string",
  "execution_time": 0.0,
  "row_count": 0,
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid report parameters
- `500`: Report generation error

**Dependencies**: Requires valid doc_id with uploaded data  
**Rate Limiting**: None  
**Idempotency**: Idempotent - same parameters produce same report

---

### POST /save_report
**Purpose**: Persist reports to DuckDB and JSON metadata  
**Business Context**: Save successful reports for reuse and navigation

**Request Schema**:
```json
{
  "doc_id": "string",
  "report_name": "string",
  "report_config": {
    "filters": {},
    "group_by": [],
    "aggregations": {},
    "sort_by": "string",
    "sort_order": "string",
    "limit": 0
  },
  "description": "string",
  "is_favorite": false
}
```

**Response Schema**:
```json
{
  "success": true,
  "report_id": 0,
  "message": "string",
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid report data
- `500`: Database save error

**Dependencies**: Requires valid doc_id  
**Rate Limiting**: None  
**Idempotency**: Not idempotent - creates new report record

---

### GET /saved_reports
**Purpose**: Retrieve saved reports for navigation  
**Business Context**: Frontend navigation and report management

**Query Parameters**:
- `doc_id` (optional): Filter by document ID
- `doc_ids` (optional): Comma-separated list of document IDs

**Response Schema**:
```json
{
  "success": true,
  "reports": [
    {
      "id": 0,
      "doc_id": "string",
      "report_name": "string",
      "report_config": {},
      "description": "string",
      "is_favorite": false,
      "created_at": "string"
    }
  ],
  "error": "string"
}
```

**Status Codes**:
- `200`: Reports retrieved successfully
- `500`: Database error

---

### GET /execute_report/{report_name}
**Purpose**: Execute saved report by name  
**Business Context**: Click-to-run functionality for saved reports

**Path Parameters**:
- `report_name` (string): Name of the saved report to execute

**Response Schema**:
```json
{
  "success": true,
  "report_name": "string",
  "sql": "string",
  "rows": [[]],
  "columns": ["string"],
  "execution_time": 0.0,
  "row_count": 0,
  "error": "string"
}
```

**Error Responses**:
- `404`: Report not found
- `500`: Execution error

**Dependencies**: Requires saved report with valid configuration  
**Rate Limiting**: None  
**Idempotency**: Idempotent - same report produces same results

---

## Database Management Endpoints

### GET /tables
**Purpose**: Display database tables in HTML format  
**Business Context**: Database inspection and debugging

**Response**: HTML table showing doc_registry, saved_queries, and saved_reports

**Status Codes**:
- `200`: Tables displayed successfully
- `500`: Database error

---

### GET /check-tables
**Purpose**: Check DuckDB table structure  
**Business Context**: Database schema inspection

**Response Schema**:
```json
{
  "success": true,
  "tables": [
    {
      "name": "string",
      "columns": [
        {
          "name": "string",
          "type": "string",
          "nullable": true
        }
      ],
      "row_count": 0
    }
  ],
  "error": "string"
}
```

**Status Codes**:
- `200`: Table structure retrieved successfully
- `500`: Database error

---

### GET /doc-registry
**Purpose**: Display document registry contents  
**Business Context**: Document type management and classification

**Response Schema**:
```json
{
  "success": true,
  "documents": [
    {
      "id": 0,
      "document_type": "string",
      "document_code": "string",
      "field_patterns": {},
      "created_at": "string"
    }
  ],
  "error": "string"
}
```

**Status Codes**:
- `200`: Registry retrieved successfully
- `500`: Database error

---

## Admin Management Endpoints

### POST /delete-table
**Purpose**: Delete DuckDB data table (admin-only)  
**Business Context**: Cleanup test data and manage storage

**Request Schema**:
```json
{
  "table_name": "string"
}
```

**Response Schema**:
```json
{
  "success": true,
  "message": "string",
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid table name
- `500`: Deletion error

**Dependencies**: Requires admin privileges  
**Rate Limiting**: None  
**Idempotency**: Idempotent - deleting non-existent table is safe

---

### POST /delete-query
**Purpose**: Delete saved query (admin-only)  
**Business Context**: Cleanup test queries and manage storage

**Request Schema**:
```json
{
  "query_id": "string"
}
```

**Response Schema**:
```json
{
  "success": true,
  "message": "string",
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid query ID
- `500`: Deletion error

---

### POST /delete-report
**Purpose**: Delete saved report (admin-only)  
**Business Context**: Cleanup test reports and manage storage

**Request Schema**:
```json
{
  "report_id": "string"
}
```

**Response Schema**:
```json
{
  "success": true,
  "message": "string",
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid report ID
- `500`: Deletion error

---

### POST /delete-doc-metadata
**Purpose**: Delete document registry entry (admin-only)  
**Business Context**: Cleanup test document metadata and manage storage

**Request Schema**:
```json
{
  "doc_id": "string"
}
```

**Response Schema**:
```json
{
  "success": true,
  "message": "string",
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid doc ID
- `500`: Deletion error

---

## Navigation and Favorites Endpoints

### GET /queries
**Purpose**: Get all queries for SuperMenu navigation  
**Business Context**: Global query navigation across all documents

**Response Schema**:
```json
{
  "success": true,
  "queries": [
    {
      "id": 0,
      "doc_id": "string",
      "query_name": "string",
      "description": "string",
      "is_favorite": false,
      "created_at": "string"
    }
  ],
  "error": "string"
}
```

**Status Codes**:
- `200`: Queries retrieved successfully
- `500`: Database error

---

### GET /reports
**Purpose**: Get all reports for SuperMenu navigation  
**Business Context**: Global report navigation across all documents

**Response Schema**:
```json
{
  "success": true,
  "reports": [
    {
      "id": 0,
      "doc_id": "string",
      "report_name": "string",
      "description": "string",
      "is_favorite": false,
      "created_at": "string"
    }
  ],
  "error": "string"
}
```

**Status Codes**:
- `200`: Reports retrieved successfully
- `500`: Database error

---

### PATCH /query/{query_id}
**Purpose**: Toggle query favorite status  
**Business Context**: Favorite management for SuperMenu

**Path Parameters**:
- `query_id` (integer): ID of the query to update

**Request Schema**:
```json
{
  "is_favorite": true
}
```

**Response Schema**:
```json
{
  "success": true,
  "message": "string",
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid query ID or request data
- `404`: Query not found
- `500`: Update error

---

### PATCH /report/{report_id}
**Purpose**: Toggle report favorite status  
**Business Context**: Favorite management for SuperMenu

**Path Parameters**:
- `report_id` (integer): ID of the report to update

**Request Schema**:
```json
{
  "is_favorite": true
}
```

**Response Schema**:
```json
{
  "success": true,
  "message": "string",
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid report ID or request data
- `404`: Report not found
- `500`: Update error

---

## Direct Execution Endpoints

### POST /query/run
**Purpose**: Execute saved query directly using SQL  
**Business Context**: Bypass LLM for deterministic results

**Request Schema**:
```json
{
  "query_name": "string",
  "doc_id": "string"
}
```

**Response Schema**:
```json
{
  "success": true,
  "query_name": "string",
  "sql": "string",
  "rows": [[]],
  "columns": ["string"],
  "execution_time": 0.0,
  "row_count": 0,
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid query name or doc_id
- `404`: Query not found
- `500`: Execution error

**Dependencies**: Requires saved query with valid SQL  
**Rate Limiting**: None  
**Idempotency**: Idempotent - same query produces same results

---

### POST /report/run
**Purpose**: Execute saved report directly using configuration  
**Business Context**: Bypass LLM for deterministic results

**Request Schema**:
```json
{
  "report_name": "string",
  "doc_id": "string"
}
```

**Response Schema**:
```json
{
  "success": true,
  "report_name": "string",
  "sql": "string",
  "rows": [[]],
  "columns": ["string"],
  "execution_time": 0.0,
  "row_count": 0,
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid report name or doc_id
- `404`: Report not found
- `500`: Execution error

**Dependencies**: Requires saved report with valid configuration  
**Rate Limiting**: None  
**Idempotency**: Idempotent - same report produces same results

---

## Analysis and Classification Endpoints

### POST /classify-document
**Purpose**: Classify document type using OpenAI LLM  
**Business Context**: Automatic document type detection and code generation

**Request Schema**:
```json
{
  "user_description": "string",
  "filename": "string",
  "metadata": {}
}
```

**Response Schema**:
```json
{
  "success": true,
  "document_type": "string",
  "document_code": "string",
  "confidence": 0.0,
  "reasoning": "string",
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid description or filename
- `500`: LLM classification error

**Dependencies**: Requires OpenAI API key  
**Rate Limiting**: None  
**Idempotency**: Not idempotent - creates new classification

---

### POST /save-analysis
**Purpose**: Save analysis results to temporary storage  
**Business Context**: Persist analysis results for session continuity

**Request Schema**:
```json
{
  "session_id": "string",
  "analysis_data": {},
  "file_metadata": {},
  "timestamp": "string"
}
```

**Response Schema**:
```json
{
  "success": true,
  "message": "string",
  "error": "string"
}
```

**Error Responses**:
- `400`: Invalid session ID or analysis data
- `500`: Save error

---

### GET /list-json-files
**Purpose**: List all available JSON files in stored_queries directory  
**Business Context**: File management and session recovery

**Response Schema**:
```json
{
  "success": true,
  "files": [
    {
      "filename": "string",
      "size": 0,
      "created": "string",
      "modified": "string"
    }
  ],
  "error": "string"
}
```

**Status Codes**:
- `200`: Files listed successfully
- `500`: Directory access error

---

### GET /get-analysis/{session_id}
**Purpose**: Retrieve saved analysis results for a session  
**Business Context**: Session recovery and analysis continuity

**Path Parameters**:
- `session_id` (string): Session identifier

**Response Schema**:
```json
{
  "success": true,
  "session_id": "string",
  "analysis_data": {},
  "file_metadata": {},
  "timestamp": "string",
  "error": "string"
}
```

**Error Responses**:
- `404`: Session not found
- `500`: Retrieval error

---

## OpenAPI 3.0 Specification

The complete OpenAPI 3.0 specification is available in `api-endpoints-openapi.yaml` for automatic LangChain tool generation.

## LangChain Integration Notes

### Tool Generation
- All endpoints can be automatically converted to LangChain tools using OpenAPI specs
- Request/response schemas provide type safety for agent interactions
- Error handling patterns enable robust agent workflows

### Agent Workflow Patterns
1. **File Upload Workflow**: `/upload` → `/autogen-chat` → `/query` or `/report`
2. **Query Workflow**: `/query` → `/save_query` → `/execute_query/{name}`
3. **Report Workflow**: `/report` → `/save_report` → `/execute_report/{name}`
4. **Navigation Workflow**: `/saved_queries` → `/execute_query/{name}`

### Error Handling
- All endpoints return consistent error response format
- HTTP status codes indicate error severity
- Error messages provide actionable information for agents

### Rate Limiting and Throttling
- File uploads: 5 files per request, 50MB per file
- No rate limiting on other endpoints for POC
- Consider implementing rate limiting for production

### Idempotency
- Query and report execution endpoints are idempotent
- File upload and save endpoints are not idempotent
- Admin delete endpoints are idempotent (safe to retry)

This comprehensive API registry enables seamless LangChain integration and provides the foundation for AI agent orchestration across the entire Excel Reporting POC system.
