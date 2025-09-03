# 🎯 AutoGen Excel Intelligence System - Implementation Plan

## 📋 Overview

This document tracks the **exact** implementation of the AutoGen-powered Excel intelligence system as specified in `agentic_imp.md` and `autgen_primer.md`. 

**CRITICAL**: Follow specifications exactly - no assumptions, no shortcuts, no "half-assed" implementations.

---

## 🏗️ Implementation Phases

### Phase 1: Core Endpoints (Priority 1)
Build the REST API endpoints that will be called by the frontend and agents.

#### 1.1 `/query` Endpoint ✅ **COMPLETED**
- **Type**: POST
- **Purpose**: Natural language → SQL → DuckDB execution
- **Input**: `doc_id`, `query_text`, `schema`, `metadata`, `datetime_context`
- **Output**: `sql`, `rows`, `columns`, `summary`
- **Requirements**:
  - ✅ LLM constructs SQL from natural language
  - ✅ Execute via `duckdb.sql(...)`
  - ✅ Auto-save as `temp_query` if no name provided
  - ✅ Return structured results
- **Status**: **FULLY TESTED** with real financial data
- **Test Results**: 
  - ✅ Simple aggregation: $18,797,994.51 total
  - ✅ Filtered queries: 75 transactions > $1000
  - ✅ Group by queries: Investment $6.18M, Revenue $6.65M, Expense $5.97M

#### 1.2 `/report` Endpoint ✅ **COMPLETED**
- **Type**: POST
- **Purpose**: Generate reports with filters, grouping, formatting
- **Input**: `doc_id`, `report_name`, `sql`, `filters`, `group_by`, `format`, `output_type`
- **Output**: HTML, XLSX, or JSON with comprehensive metadata
- **Requirements**:
  - ✅ Takes SQL query as input (not LLM generation)
  - ✅ Use `pandas` + `duckdb` for data logic
  - ✅ Support `plotly`, `matplotlib`, `openpyxl`, `jinja2`
  - ✅ Fallback name: `temp_report`
  - ✅ File naming: `{duckdb_table_name}_{timestamp}.xlsx`
  - ✅ Auto-save to DuckDB and JSON metadata
  - ✅ Comprehensive return dictionary for next agent
- **Status**: **FULLY TESTED** with real financial data
- **Test Results**:
  - ✅ HTML output: Generated reports with data tables and styling
  - ✅ XLSX output: Created Excel files with proper naming convention
  - ✅ Auto-save: Reports saved to `saved_reports` table and JSON metadata
  - ✅ Return format: Comprehensive dictionary with all agent-required data

#### 1.3 `/save_query` Endpoint ✅ **COMPLETED**
- **Type**: POST
- **Purpose**: Persist queries to DuckDB and .json
- **Input**: `doc_id`, `query_text`, `sql`, `query_name`, `tags`
- **Requirements**:
  - ✅ Save to DuckDB `saved_queries` table
  - ✅ Append to document's `.json` file
  - ✅ Store: doc_id, query_name, sql, query_text, tags, timestamp
- **Status**: **FULLY TESTED** with real data
- **Test Results**:
  - ✅ Successfully saves queries to DuckDB saved_queries table
  - ✅ Appends query data to document JSON metadata
  - ✅ Input validation working correctly (400 errors for missing fields)
  - ✅ Returns comprehensive success response with save status

#### 1.4 `/save_report` Endpoint ✅ **COMPLETED**
- **Type**: POST  
- **Purpose**: Persist reports to DuckDB and .json
- **Input**: `doc_id`, `report_name`, `sql`, `filters`, `group_by`, `format`, `chart`, `description`
- **Requirements**:
  - ✅ Save to DuckDB `saved_reports` table
  - ✅ Append to document's `.json` file
  - ✅ Store: doc_id, report_name, sql, filters, group_by, format, chart, description, timestamp
- **Status**: **FULLY TESTED** with real data
- **Test Results**:
  - ✅ Successfully saves reports to DuckDB saved_reports table
  - ✅ Appends report data to document JSON metadata
  - ✅ Input validation working correctly (400 errors for missing fields)
  - ✅ Returns comprehensive success response with save status
  - ✅ Handles all report formats (table, chart) and chart types (bar, pie)
- **Use Cases**:
  - ✅ Save pre-configured reports without generating them
  - ✅ Rename existing reports (change "temp_report" to custom name)
  - ✅ Agent workflows for explicit save operations
  - ✅ Manual report configuration and saving

#### 1.5 `/saved_queries` Endpoint ✅ **COMPLETED**
- **Type**: GET
- **Purpose**: Retrieve saved queries for navigation dropdown
- **Params**: `doc_id` (string) OR `doc_ids` (comma-separated string)
- **Query Logic**: `WHERE doc_id IN (provided_doc_ids)`
- **Output**: List of query records with query_names, timestamps, and basic metadata
- **Requirements**:
  - ✅ Support single doc_id or multiple doc_ids (comma-separated)
  - ✅ Return navigation-friendly data structure
  - ✅ Input validation for missing parameters
  - ✅ Proper error handling with 400/500 status codes
- **Status**: **FULLY TESTED** with real data
- **Test Results**:
  - ✅ Single doc_id: Found 1 query for projects document
  - ✅ Multiple doc_ids: Found 7 queries across 2 documents
  - ✅ Input validation: Proper 400 errors for missing parameters
  - ✅ Navigation data structure: Perfect format for frontend dropdowns
- **Use Cases**:
  - ✅ Frontend navigation: "Available Queries" dropdown
  - ✅ Agent memory: Find relevant past queries for loaded documents
- **Frontend Integration**: Agent sends doc_ids from localStorage

#### 1.6 `/saved_reports` Endpoint ✅ **COMPLETED**
- **Type**: GET
- **Purpose**: Retrieve saved reports for navigation dropdown
- **Params**: `doc_id` (string) OR `doc_ids` (comma-separated string)
- **Query Logic**: `WHERE doc_id IN (provided_doc_ids)`
- **Output**: List of report records with report_names, timestamps, and basic metadata
- **Requirements**:
  - ✅ Support single doc_id or multiple doc_ids (comma-separated)
  - ✅ Return navigation-friendly data structure
  - ✅ Input validation for missing parameters
  - ✅ Proper error handling with 400/500 status codes
- **Status**: **FULLY TESTED** with real data
- **Test Results**:
  - ✅ Single doc_id: Found 4 reports for projects document
  - ✅ Multiple doc_ids: Found 11 reports across 2 documents
  - ✅ Input validation: Proper 400 errors for missing parameters
  - ✅ Navigation data structure: Perfect format for frontend dropdowns
- **Use Cases**:
  - ✅ Frontend navigation: "Available Reports" dropdown
  - ✅ Agent memory: Find relevant past reports for loaded documents
- **Frontend Integration**: Agent sends doc_ids from localStorage

#### 1.7 `/execute_query/{query_name}` Endpoint
- **Type**: GET
- **Purpose**: Execute a saved query by name and return results

- **Params**: `query_name` (path parameter - string) - e.g., "Lyft", "Disney clients", "temp_query"
- **Behavior**:
  - Fetch query details from `saved_queries` table by `query_name`
  - Execute the stored SQL via DuckDB
  - Return results in same format as `/query` endpoint
  - Update `use_count` and `last_used` timestamp
  - Handle missing query_name with 404 error
- **Output**: `sql`, `rows`, `columns`, `summary`, `query_id`, `query_name`, `execution_time`
- **Usage Patterns**:
  - **Frontend Navigation Click-to-Run**: User clicks saved query in navigation dropdown
  - **Agent Programmatic Execution**: ConversationalAgent re-runs past queries by name (e.g., "run the Lyft query")
  - **Quick Access**: Frequently used queries without re-typing
- **Error Handling**:
  - 404: Query name not found
  - 500: SQL execution error
  - 400: Invalid query_name format

#### 1.8 `/execute_report/{report_id}` Endpoint
- **Type**: GET
- **Purpose**: Execute a saved report by ID and return formatted output
- **Params**: `report_id` (path parameter - integer)
- **Behavior**:
  - Fetch report details from `saved_reports` table by `report_id`
  - Execute the stored SQL via DuckDB
  - Generate output using `report_builder.py`
  - Return formatted results (HTML, XLSX, or JSON)
  - Update `generation_count` and `last_generated` timestamp
  - Handle missing report_id with 404 error
- **Output**: Same format as `/report` endpoint with execution metadata
- **Usage Patterns**:
  - **Frontend Navigation Click-to-Run**: User clicks saved report in navigation dropdown
  - **Agent Programmatic Execution**: ConversationalAgent re-runs past reports
  - **Download Links**: For long results, provide download URLs
  - **Report Regeneration**: Update reports with fresh data
- **Error Handling**:
  - 404: Report ID not found
  - 500: SQL execution or report generation error
  - 400: Invalid report_id format

---

### Phase 2: Utility Modules (Priority 2)
Build the supporting utility modules that endpoints and agents will use.

#### 2.1 `duckdb_manager.py`
- **Purpose**: Create/query `saved_queries`, `saved_reports`, `doc_registry`
- **Functions**:
  - `create_query_table()`
  - `create_report_table()`
  - `create_doc_registry_table()`
  - Store full SQL and report parameters (NOT normalized)

#### 2.2 `report_builder.py`
- **Purpose**: Accept filters + schema + data → return output in desired format
- **Called by**: `ReportAgent`
- **Support**: HTML, XLSX, JSON, chart formats
- **Dependencies**: `pandas`, `duckdb`, `plotly`, `matplotlib`, `openpyxl`, `jinja2`

#### 2.3 `agent_router.py`
- **Purpose**: Route requests to appropriate agents
- **Function**: `route_request(agent_input: Dict) -> str`
- **Output**: Name of agent to route to
- **Logic**: Intent detection and routing

#### 2.4 `json_store.py`
- **Purpose**: Load/save document metadata to .json files
- **Functions**:
  - `save_metadata(doc_id, metadata)`
  - `load_metadata(doc_id)`
  - `append_query_to_metadata(doc_id, query_data)`
  - `append_report_to_metadata(doc_id, report_data)`

---

### Phase 3: AutoGen Agents (Priority 3)
Build the AutoGen agents that will handle conversational interactions.

#### 3.1 `ChatAgent` (ConversableAgent)
- **File**: `chat_agent.py`
- **Purpose**: First interface with user
- **Behavior**:
  - Accept natural language input from frontend
  - Parse prompt into structured dict
  - Inject localStorage context (schema, record count)
  - Send to `OrchestrationAgent`

#### 3.2 `OrchestrationAgent` (ToolAgent)
- **File**: `orchestration_agent.py`
- **Purpose**: Central router
- **Behavior**:
  - Accept structured dict from `ChatAgent`
  - Call `route_request()` from `agent_router.py`
  - Route to: `QueryAgent`, `ReportAgent`, `UploadAgent`, `MemoryAgent`
  - Use LLM for disambiguation if unclear
  - Enforce fallback names: `temp_query`, `temp_report`

#### 3.3 `QueryAgent` (ConversableAgent)
- **File**: `query_agent.py`
- **Purpose**: Convert query intent into SQL + response
- **Behavior**:
  - Receive: `doc_id`, `query_text`, `schema`, `metadata`
  - Prompt LLM with full schema, user question, document metadata
  - Execute SQL via DuckDB
  - Return: `sql`, `rows`, `columns`, `summary`
  - Auto-save as `temp_query` unless named

#### 3.4 `ReportAgent` (ConversableAgent)
- **File**: `report_agent.py`
- **Purpose**: Interpret and build grouped/filtered reports
- **Behavior**:
  - Accept report specification
  - Prompt LLM to interpret vague titles and determine logic
  - Use `report_builder.py` for assembly
  - Save to `.json` and `saved_reports`
  - Return HTML, XLSX, or JSON based on `output_type`

#### 3.5 `UploadAgent` (ConversableAgent)
- **File**: `upload_agent.py`
- **Purpose**: Metadata enrichment after file upload
- **Behavior**:
  - Called after `/upload` endpoint succeeds
  - Prompt user: "What is this file?", "Add notes, label, project ID"
  - Update `.json` metadata via `save_metadata()`
  - Update `doc_registry` for file type → description, usage context

#### 3.6 `MemoryAgent` (ToolAgent)
- **File**: `memory_agent.py`
- **Purpose**: Fetch saved queries/reports
- **Behavior**:
  - Accept lookup dict: `doc_id`, `query_name`, `tags`
  - Search DuckDB: `saved_queries`, `saved_reports`
  - Return full SQL or report definition

---

### Phase 4: Integration Testing (Priority 4)
End-to-end testing of the complete system.

#### 4.1 Endpoint Testing
- Test each endpoint with mock data
- Verify DuckDB operations
- Verify .json file operations
- Test error handling

#### 4.2 Agent Testing
- Test each agent with mock input dicts
- Verify agent conversations
- Test routing logic
- Verify fallback behaviors

#### 4.3 End-to-End Workflow Testing
- Upload file → ChatAgent → OrchestrationAgent → QueryAgent → Results
- Upload file → ChatAgent → OrchestrationAgent → ReportAgent → Report
- Test saved queries/reports retrieval
- Test localStorage integration

---

## 📁 Required Project Structure

```
backend/
├── app.py                    # FastAPI endpoints (existing + new)
├── agents/
│   ├── chat_agent.py         # ChatAgent
│   ├── orchestration_agent.py # OrchestrationAgent  
│   ├── query_agent.py        # QueryAgent
│   ├── report_agent.py       # ReportAgent
│   ├── upload_agent.py       # UploadAgent
│   └── memory_agent.py       # MemoryAgent
├── utils/
│   ├── agent_router.py       # route_request()
│   ├── duckdb_manager.py     # db operations
│   ├── duckdb_utils.py       # ensure tables
│   ├── json_store.py         # JSON load/save
│   └── report_builder.py     # pandas + chart logic
├── excel_processor.py        # existing file processing
└── tests/
    ├── test_endpoints.py     # endpoint tests
    └── test_agents.py        # agent tests
```

---

## 🎯 Success Criteria

### Phase 1 Complete When:
- [x] `/query` endpoint implemented and tested ✅
- [x] `/report` endpoint implemented and tested ✅
- [x] `/save_query` endpoint implemented and tested ✅
- [x] `/save_report` endpoint implemented and tested ✅
- [x] `/saved_queries` endpoint implemented and tested ✅
- [x] `/saved_reports` endpoint implemented and tested ✅
- [x] DuckDB tables created and populated ✅
- [x] .json metadata files working ✅
- [x] Error handling implemented ✅
- [ ] `/execute_query/{query_id}` endpoint implemented and tested
- [ ] `/execute_report/{report_id}` endpoint implemented and tested
- [ ] API documentation complete

### Phase 2 Complete When:
- [ ] All utility modules implemented
- [ ] Unit tests for each utility
- [ ] Integration with endpoints verified
- [ ] Error handling and validation

### Phase 3 Complete When:
- [ ] All 6 agents implemented with AutoGen
- [ ] Agent conversations working
- [ ] Routing logic functional
- [ ] Fallback behaviors working
- [ ] Agent tests passing

### Phase 4 Complete When:
- [ ] End-to-end workflows functional
- [ ] Frontend integration working
- [ ] Performance acceptable
- [ ] Error scenarios handled
- [ ] Documentation complete

---

## 🚨 Critical Requirements

1. **Follow specifications exactly** - no assumptions or shortcuts
2. **30% comment ratio** - document everything thoroughly
3. **Test each component** before proceeding to next
4. **Use exact input/output formats** from specifications
5. **Implement all storage logic** (DuckDB + .json)
6. **Handle all error cases** gracefully
7. **Use localStorage** for frontend integration
8. **Implement fallback names** (`temp_query`, `temp_report`)

---

## 📝 Next Steps

**Phase 1 Progress: 6/8 endpoints completed (75% complete)**

✅ **Completed:**
- `/query` endpoint - Natural language to SQL with DuckDB execution
- `/report` endpoint - Generate reports with SQL input and multiple output formats
- `/save_query` endpoint - Persist queries to DuckDB and .json metadata
- `/save_report` endpoint - Persist reports to DuckDB and .json metadata
- `/saved_queries` endpoint - Navigation support for queries (single/multiple doc_ids)
- `/saved_reports` endpoint - Navigation support for reports (single/multiple doc_ids)

🔄 **Next: Phase 1.7 & 1.8 Execution Endpoints**
- **Purpose**: Execute saved queries and reports by ID for dual usage patterns
- **Type**: GET with path parameters
- **Dual Usage**: Frontend click-to-run + Agent programmatic execution
- **Behavior**: Fetch details, execute SQL, return results, update usage stats
- **Output**: Same format as original endpoints with execution metadata
- **Use Cases**: Navigation panel clicks, agent re-execution, quick access

**Remaining Phase 1 endpoints:**
- `/execute_query/{query_id}` endpoint (GET) - Execute saved queries by ID
- `/execute_report/{report_id}` endpoint (GET) - Execute saved reports by ID

**Ready to proceed to Phase 1.7: `/execute_query/{query_id}` endpoint for execution functionality.**
