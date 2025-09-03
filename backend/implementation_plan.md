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

#### 1.7 `/execute_query/{query_name}` Endpoint ✅ **COMPLETED**
- **Type**: GET
- **Purpose**: Execute a saved query by name and return results
- **Params**: `query_name` (path parameter - string) - e.g., "Lyft", "Disney clients", "temp_query"
- **Behavior**:
  - ✅ Fetch query details from `saved_queries` table by `query_name`
  - ✅ Load JSON metadata to get correct `duckdb_table_name`
  - ✅ Fix SQL query to use correct table name from JSON
  - ✅ Execute the stored SQL via DuckDB
  - ✅ Return results in same format as `/query` endpoint
  - ✅ Update `use_count` and `last_used` timestamp
  - ✅ Handle missing query_name with 404 error
- **Output**: `sql`, `rows`, `columns`, `summary`, `query_id`, `query_name`, `execution_time`
- **Status**: **FULLY TESTED** with real data
- **Test Results**:
  - ✅ `temp_query`: Found 2 Disney projects, table name corrected from JSON
  - ✅ `total_transactions`: Returned $18,797,994.51 total, table name corrected from JSON
  - ✅ JSON metadata integration: Correctly loads `duckdb_table_name` and fixes SQL
  - ✅ Error handling: Proper 404 for missing queries, 500 for SQL errors
  - ✅ Usage tracking: Updates statistics on execution
- **Usage Patterns**:
  - ✅ **Frontend Navigation Click-to-Run**: User clicks saved query in navigation dropdown
  - ✅ **Agent Programmatic Execution**: ConversationalAgent re-runs past queries by name (e.g., "run the Lyft query")
  - ✅ **Quick Access**: Frequently used queries without re-typing
- **Error Handling**:
  - ✅ 404: Query name not found
  - ✅ 500: SQL execution error
  - ✅ 400: Invalid query_name format

#### 1.8 `/execute_report/{report_name}` Endpoint ✅ **COMPLETED**
- **Type**: GET
- **Purpose**: Execute a saved report by name and return formatted output
- **Params**: `report_name` (path parameter - string) - e.g., "temp_report", "Financial Summary Report"
- **Behavior**:
  - Fetch report details from `saved_reports` table by `report_name`
  - Load document JSON metadata to get correct `duckdb_table_name`
  - Dynamically correct SQL table name using regex substitution
  - Execute the corrected SQL via DuckDB
  - Generate report output with summary and metadata
  - Update `generation_count` and `last_generated` timestamp
  - Handle missing report_name with 404 error
- **Output**: Same format as `/report` endpoint with execution metadata
- **Status**: **FULLY TESTED** with real data
- **Test Results**:
  - ✅ `temp_report`: 23 rows with client project counts and budgets
  - ✅ `Financial Summary Report`: 3 transaction types (Investment: 23, Revenue: 26, Expense: 26)
  - ✅ Table name correction working: Uses correct table from JSON metadata
  - ✅ Usage tracking: Updates generation_count and last_generated timestamps
- **Usage Patterns**:
  - **Frontend Navigation Click-to-Run**: User clicks saved report in navigation dropdown
  - **Agent Programmatic Execution**: ConversationalAgent re-runs past reports by name
  - **Download Links**: For long results, provide download URLs
  - **Report Regeneration**: Update reports with fresh data
- **Error Handling**:
  - 404: Report name not found
  - 500: SQL execution or report generation error
  - 400: Invalid report_name format

---

### Phase 2: Utility Modules (Priority 2)
Build the supporting utility modules that endpoints and agents will use.

#### 2.1 `duckdb_manager.py` ✅ **COMPLETED**
- **Purpose**: Create/query `saved_queries`, `saved_reports`, `doc_registry`
- **Functions**:
  - ✅ `create_query_table()` - Creates saved_queries table
  - ✅ `create_report_table()` - Creates saved_reports table
  - ✅ `save_query()` - Saves queries to DuckDB
  - ✅ `save_report()` - Saves reports to DuckDB
  - ✅ `get_saved_queries()` - Retrieves queries with filtering
  - ✅ `get_saved_reports()` - Retrieves reports with filtering
  - ✅ `get_query_by_name()` - Gets query by name (for execute endpoints)
  - ✅ `update_query_usage_stats()` - Updates usage statistics
  - ✅ `ensure_all_tables_exist()` - Creates all required tables
- **Status**: **FULLY IMPLEMENTED** with comprehensive functionality

#### 2.2 `report_builder.py` ✅ **COMPLETED**
- **Purpose**: Accept filters + schema + data → return output in desired format
- **Called by**: `ReportAgent`
- **Support**: HTML, XLSX, JSON, chart formats
- **Dependencies**: `pandas`, `duckdb`, `plotly`, `matplotlib`, `openpyxl`, `jinja2`
- **Functions**:
  - ✅ `build_report()` - Main report generation function
  - ✅ `generate_html_report()` - HTML output with charts
  - ✅ `generate_xlsx_report()` - Excel output with openpyxl
  - ✅ `generate_json_report()` - JSON output
  - ✅ `create_chart()` - Chart generation with plotly/matplotlib
  - ✅ `validate_report_config()` - Configuration validation
- **Status**: **FULLY IMPLEMENTED** with all required functionality

#### 2.3 `agent_router.py` ✅ **COMPLETED**
- **Purpose**: Route requests to appropriate agents
- **Function**: `route_request(agent_input: Dict) -> str`
- **Output**: Name of agent to route to
- **Logic**: Intent detection and routing
- **Functions**:
  - ✅ `route_request()` - Main routing function with pattern-based intent detection
  - ✅ `analyze_intent()` - Intent detection using regex patterns
  - ✅ `validate_agent_input()` - Input validation
  - ✅ `get_routing_confidence()` - Confidence scoring for routing decisions
  - ✅ `get_available_agents()` - List available agents
- **Pattern Matching**: 
  - ✅ Query patterns: Financial questions, data requests
  - ✅ Report patterns: Report generation, charts, summaries
  - ✅ Upload patterns: File description, metadata updates
  - ✅ Memory patterns: Saved queries/reports retrieval
- **Test Results**: **100% success rate** on all test cases
- **Status**: **FULLY IMPLEMENTED** with comprehensive pattern matching

#### 2.4 `json_store.py` ✅ **COMPLETED**
- **Purpose**: Load/save document metadata to .json files
- **Functions**:
  - ✅ `save_metadata(doc_id, metadata)` - Save document metadata
  - ✅ `load_metadata(doc_id)` - Load document metadata
  - ✅ `append_query_to_metadata(doc_id, query_data)` - Add query to metadata
  - ✅ `append_report_to_metadata(doc_id, report_data)` - Add report to metadata
  - ✅ `get_doc_id_from_filename(filename)` - Generate doc_id from filename
  - ✅ `list_available_doc_ids()` - List all available documents
- **Status**: **FULLY IMPLEMENTED** with all required functionality

---

### Phase 3: AutoGen Agents (Priority 3)
Build the AutoGen agents that will handle conversational interactions. We currently have a few agents - this is a replacement for those agent. We are implementing AutoGen framework in totality.

#### 3.0 Document Classification System ✅ **NEW FEATURE**
- **Purpose**: Automatic document type detection and classification
- **Workflow**:
  1. **Upload Processing**: Each document uploaded → compare field string to `doc_registry`
  2. **Existing Document Type**: If field pattern matches existing record:
     - Increment `latest_version` in `doc_registry` (e.g., 1.0 → 1.1)
     - Assign incremented version to uploaded document's JSON
     - Set `ready_for_sql_agent: true`
  3. **New Document Type**: If field pattern not found:
     - Create new record in `doc_registry` with `latest_version = 1.0`
     - Assign version `1.0` to uploaded document's JSON
     - Set `ready_for_sql_agent: true`
- **Implementation**: Integrate into existing upload endpoint and AutoGen agent flow
- **Benefits**: 
  - Preload queries/reports based on document type
  - Support weekly uploads of same document type (e.g., "Company Financial Report")
  - Automatic version management
  - No manual classification needed 

#### 3.1 `ChatAgent` (ConversableAgent)
- **File**: `chat_agent.py`
- **Purpose**: First interface with user
- **Behavior**:
  - Accept natural language input from frontend
  - Parse prompt into structured dict
  - Inject localStorage context (schema, record count, duckdb table location)
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
- [x] `/execute_query/{query_name}` endpoint implemented and tested ✅
- [x] `/execute_report/{report_name}` endpoint implemented and tested ✅
- [x] DuckDB tables created and populated ✅
- [x] .json metadata files working ✅
- [x] Error handling implemented ✅
- [ ] API documentation complete

### Phase 2 Complete When:
- [x] All utility modules implemented ✅
- [x] Unit tests for each utility ✅
- [x] Integration with endpoints verified ✅
- [x] Error handling and validation ✅

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

**Phase 1 Progress: 8/8 endpoints completed (100% complete) 🎉**
**Phase 2 Progress: 4/4 utility modules completed (100% complete) 🎉**

✅ **Phase 1 Completed:**
- `/query` endpoint - Natural language to SQL with DuckDB execution
- `/report` endpoint - Generate reports with SQL input and multiple output formats
- `/save_query` endpoint - Persist queries to DuckDB and .json metadata
- `/save_report` endpoint - Persist reports to DuckDB and .json metadata
- `/saved_queries` endpoint - Navigation support for queries (single/multiple doc_ids)
- `/saved_reports` endpoint - Navigation support for reports (single/multiple doc_ids)
- `/execute_query/{query_name}` endpoint - Execute saved queries by name with JSON metadata integration
- `/execute_report/{report_name}` endpoint - Execute saved reports by name with JSON metadata integration

✅ **Phase 2 Completed:**
- `duckdb_manager.py` - Complete DuckDB operations with all required functions
- `report_builder.py` - Full report generation with HTML, XLSX, JSON, and chart support
- `agent_router.py` - Pattern-based intent detection with 100% test success rate
- `json_store.py` - Complete JSON metadata management with all required functions

🎯 **Phase 1 & 2 Complete! All Core Endpoints and Utility Modules Implemented and Tested**

**Key Achievements:**
- **Dual Usage Patterns**: Both frontend click-to-run and agent programmatic execution
- **Dynamic Table Correction**: SQL queries automatically use correct table names from JSON metadata
- **Usage Tracking**: Query and report execution statistics maintained
- **Comprehensive Testing**: All endpoints and utilities tested with real data and edge cases
- **Error Handling**: Proper HTTP status codes and error messages
- **JSON Integration**: Seamless metadata persistence and retrieval
- **Pattern-Based Routing**: High-accuracy agent routing with regex pattern matching
- **Report Generation**: Full support for multiple output formats with chart generation

**Ready to proceed to Phase 3: AutoGen Agents Implementation**
