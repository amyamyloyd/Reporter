# 🧠 Agentic Backend Implementation Plan for Cursor

This document defines **every endpoint, every agent, and every utility module** used in the AutoGen-powered Excel intelligence system. It combines the full backend and utility specifications into one complete reference for Cursor AI.

⚠️  Cursor must:

* Never deduplicate or compress markdown structure.
* Never assume context is shared between endpoints or agents.
* Always repeat input/output formats per endpoint.
* Never skip internal storage logic (e.g. `.json`, `duckdb`, `localStorage`).

---

## ✅ Endpoint: `/upload`

**Type**: POST
**Exists**: ✅ Yes

### Purpose

Accept Excel file(s), process content, and persist:

* Table content → DuckDB
* Metadata → `.json` file
* Registry → `doc_registry` table (tracks document types only)
* Assign and store a unique `doc_id` per uploaded file (used everywhere else)

### Responsibilities

* Generate a `doc_id` during upload based on file naming convention
* Store file metadata using `json_store.py` (see below)
* Record document **type** in `doc_registry`
* Return `doc_id` to frontend and write to `localStorage`

### Output:

```json
{
  "doc_id": "hospital_ledger_fy2024_001",
  "status": "uploaded",
  "record_count": 1220,
  "fields": ["Vendor", "Date", "Amount"],
  "json_filename": "hospital_ledger_fy2024_001.json"
}
```

---

## 🔧 New Endpoints to Build

### `/query`

**Type**: POST

### Purpose

Receive a query in natural language or structured input → generate SQL → run via DuckDB → return results.

### Input

```json
{
  "doc_id": "hospital_ledger_fy2024_001",
  "query_text": "How much did we spend on Vendor X in Q2?",
  "schema": ["Vendor", "Date", "Amount"],
  "metadata": {"record_count": 1200, "created": "2024-01-01"},
  "datetime_context": {"now": "2025-09-02", "current_quarter": "Q3", "last_quarter": "Q2"}
}
```

### Output

```json
{
  "sql": "SELECT SUM(Amount) FROM hospital_ledger_fy2024_001 WHERE Vendor = 'Vendor X' AND Quarter = 'Q2'",
  "rows": [[124000.50]],
  "columns": ["Total Amount"],
  "summary": "We spent $124,000.50 on Vendor X in Q2."
}
```

### Responsibilities

* LLM must construct SQL query based on input text + schema + datetime context
* SQL executed with `duckdb.sql(...)`
* Results passed back to frontend
* Query may be optionally saved to `/save_query`
* If no `query_name`, default to `"temp_query"` and write to DuckDB

---

### `/report`

**Type**: POST

### Purpose

Generate report using filters, grouping, formatting, and natural language title.

### Input

```json
{
  "doc_id": "hospital_ledger_fy2024_001",
  "report_name": "Weekly Vendor Spend",
  "filters": {"vendor": "Vendor X", "quarter": "Q2"},
  "group_by": ["Week"],
  "format": "chart",
  "output_type": "html"
}
```

### Output

* HTML or downloadable `.xlsx`
* JSON summary if requested

### Responsibilities

* LLM must interpret vague `report_name` if present
* Build report logic using:

  * `pandas` + `duckdb`
  * `plotly` or `matplotlib`
  * `openpyxl` or `xlsxwriter`
  * `jinja2` + `html` for web output
* Fallback: use name `"temp_report"` if name is not provided

---

### `/save_query`

**Type**: POST

### Input

```json
{
  "doc_id": "hospital_ledger_fy2024_001",
  "query_text": "How much did we spend on Vendor X in Q2?",
  "sql": "SELECT SUM(Amount)...",
  "query_name": "Quarterly Vendor Spend",
  "tags": ["vendor", "q2", "spending"]
}
```

### Behavior

* Save record to DuckDB `saved_queries` table
* Also append metadata to document's `.json` file
* Fields stored: doc\_id, query\_name, sql, query\_text, tags, timestamp

---

### `/save_report`

**Type**: POST

### Input

```json
{
  "doc_id": "hospital_ledger_fy2024_001",
  "report_name": "Weekly Vendor Spend",
  "sql": "...",
  "filters": {"vendor": "Vendor X"},
  "group_by": ["Week"],
  "format": "table",
  "chart": "bar",
  "description": "Summarizes weekly spending by vendor."
}
```

### Behavior

* Save to `saved_reports` table in DuckDB
* Also append to document’s `.json`

---

### `/saved_queries` (GET)

* Params: `doc_id`, `tags`, `date_range`
* Output: all matching entries from `saved_queries`

### `/saved_reports` (GET)

* Params: `doc_id`, `tags`, `output_type`
* Output: all matching entries from `saved_reports`

---

### `/execute_query/{query_name}` (GET)

**Type**: GET

### Purpose

Execute a saved query by name and return results. Supports both frontend click-to-run and agent programmatic execution.

### Input

* Path parameter: `query_name` (string) - e.g., "Lyft", "Disney clients", "temp_query"

### Output

```json
{
  "sql": "SELECT SUM(Amount) FROM hospital_ledger_fy2024_001 WHERE Vendor = 'Vendor X'",
  "rows": [[124000.50]],
  "columns": ["Total Amount"],
  "summary": "We spent $124,000.50 on Vendor X in Q2.",
  "query_id": 123,
  "query_name": "Lyft",
  "execution_time": "2025-09-02T10:30:00Z"
}
```

### Responsibilities

* Fetch query details from `saved_queries` table by `query_name`
* Execute the stored SQL via DuckDB
* Return results in same format as `/query` endpoint
* Update `use_count` and `last_used` timestamp
* Handle missing query_name with 404 error

### Usage Patterns

1. **Frontend Navigation Click-to-Run**: User clicks saved query in navigation dropdown
2. **Agent Programmatic Execution**: ConversationalAgent re-runs past queries by name (e.g., "run the Lyft query")

---

### `/execute_report/{report_id}` (GET)

**Type**: GET

### Purpose

Execute a saved report by ID and return formatted output. Supports both frontend click-to-run and agent programmatic execution.

### Input

* Path parameter: `report_id` (integer)

### Output

* HTML, XLSX, or JSON (same format as `/report` endpoint)
* Includes report metadata and execution details

### Responsibilities

* Fetch report details from `saved_reports` table by `report_id`
* Execute the stored SQL via DuckDB
* Generate output using `report_builder.py`
* Return formatted results (HTML, XLSX, or JSON)
* Update `generation_count` and `last_generated` timestamp
* Handle missing report_id with 404 error

### Usage Patterns

1. **Frontend Navigation Click-to-Run**: User clicks saved report in navigation dropdown
2. **Agent Programmatic Execution**: ConversationalAgent re-runs past reports
3. **Download Links**: For long results, provide download URLs

---

## 🤖 Agents to Implement

### `ChatAgent`

Type: ConversableAgent
Purpose: Entry point for user prompt

### Responsibilities

* Accept natural language prompt
* Enrich prompt with localStorage metadata (doc\_id, schema)
* Send structured request to `OrchestrationAgent`

---

### `OrchestrationAgent`

Type: ToolAgent
Purpose: Route intent to proper downstream agent

### Responsibilities

* Accept structured dict (intent, doc\_id, context)
* Use `agent_router.route_request()` to:

  * → `QueryAgent`
  * → `ReportAgent`
  * → `UploadAgent`
  * → `MemoryAgent`
  * Or ask LLM if unclear

---

### `QueryAgent`

Type: ConversableAgent

### Input

Same as `/query` endpoint input JSON

### Responsibilities

* Construct SQL via LLM
* Run query via `duckdb`
* Return rows + columns + summary
* Fallback name: `temp_query`
* Save to `.json` and `saved_queries`

---

### `ReportAgent`

Type: ConversableAgent

### Input

Same as `/report` endpoint input JSON

### Responsibilities

* Construct logic via LLM (groupings, filters)
* Build output via `report_builder.py`
* Save to `.json` and `saved_reports`
* Return HTML, XLSX, or JSON depending on `output_type`

---

### `UploadAgent`

Type: ConversableAgent

### Responsibilities

* Ask user to label the file and assign purpose
* Update `doc_registry`
* Store metadata to `.json`

---

### `MemoryAgent`

Type: ToolAgent

### Responsibilities

* Fetch saved reports and queries by `doc_id`, `tags`, `query_name`

---

## 🛠️ Utilities


### `duckdb_manager.py`

**Purpose**: Create/query `saved_queries`, `saved_reports`, `doc_registry`

* Must implement `create_query_table()`, `create_report_table()`
* Store full SQL and report parameters (NOT normalized)

### `report_builder.py`

**Purpose**: Accept filters + schema + data → return output in desired format

* Called by `ReportAgent`
* Must support HTML, XLSX, JSON, chart formats

### `agent_router.py`

**Purpose**: Move if/then routing logic into separate utility

* `route_request(agent_input: Dict) -> str`
* Output: name of agent to route to

---

## ☑️ Implementation Requirements for Cursor

* Do not hallucinate.
* Do not remove field definitions.
* Do not skip `doc_id` logic.
* Save full records to DuckDB and .json.
* Use localStorage on frontend to pass `doc_id` into ChatAgent prompts.
* Implement every agent as a distinct class using pyautogen.

Let me know when ready to:

* Build Autogen orchestration config
* Add `/query` and `QueryAgent`
* Write test case runners for each agent
