# 🧠 Autogen Primer for Cursor AI

This document defines the standards, setup, and implementation rules for building an AutoGen-based system with multiple agents. It is specifically written for **Cursor AI** to implement in code, and must be followed **exactly**.

---

## ✅ Versioning and Environment

* **Python**: `>=3.10`
* **AutoGen**: `pyautogen==0.4.0` or newer (0.4.x series)
* **LLM Provider**: Configurable, with OpenAI GPT-4-turbo or Azure OpenAI endpoints
* **Installation**:

  ```bash
  pip install pyautogen
  ```
* **Project structure must support**:

  * `.env` for LLM keys
  * `config_list.json` for agent identity and model settings

---

## 🧩 Agent Types to Implement

### 1. `OrchestrationAgent`

**Type**: `ToolAgent`
**File**: `orchestration_agent.py`

**Purpose**: The central router — receives a structured dict and forwards it to the correct tool agent or conversational agent.

**Behavior**:

* Accepts a dict from `ChatAgent`
* Calls `route_request()` from `agent_router.py`
* Sends the dict to one of:

  * `QueryAgent`
  * `ReportAgent`
  * `UploadAgent`
  * `MemoryAgent`
* If ambiguous, uses LLM to disambiguate intent
* Enforces fallback names: `temp_query`, `temp_report`

---

### 2. `ChatAgent`

**Type**: `ConversableAgent`
**File**: `chat_agent.py`

**Purpose**: First interface with the user

**Behavior**:

* Accepts natural language input from frontend
* Parses prompt into structured dict:

  ```json
  {
    "doc_id": "hospital_system_fy2024",
    "query_text": "What did we spend on Vendor X in Q2?",
    "datetime_context": {"now": "2025-09-02"}
  }
  ```
* Injects localStorage context (schema, record count)
* Sends to `OrchestrationAgent`

---

### 3. `QueryAgent`

**Type**: `ConversableAgent`
**File**: `query_agent.py`

**Purpose**: Convert query intent into SQL + response

**Behavior**:

* Receives: `doc_id`, `query_text`, `schema`, `metadata`
* Prompts LLM with:

  * full schema
  * user question
  * document metadata (record count, created)
* Executes SQL via DuckDB
* Returns:

  ```json
  {
    "sql": "SELECT SUM(...)",
    "rows": [[...]],
    "columns": ["Vendor", "Amount"],
    "summary": "Total spend with Vendor X was $32,000"
  }
  ```
* All queries must be saved via `/save_query` using fallback name `temp_query` unless named

---

### 4. `ReportAgent`

**Type**: `ConversableAgent`
**File**: `report_agent.py`

**Purpose**: Interpret and build grouped/filtered reports

**Behavior**:

* Accepts:

  ```json
  {
    "doc_id": "...",
    "report_name": "Weekly Spend",
    "group_by": ["Week"],
    "filters": {"vendor": "Vendor X"},
    "output_type": "html"
  }
  ```
* Prompts LLM to:

  * Interpret vague titles
  * Determine logic and fields
* Uses `report_builder.py` to assemble:

  * `pandas` + `duckdb` for data logic
  * `plotly`, `matplotlib`, `openpyxl`, `jinja2` for rendering
* Saves:

  * Full JSON + chart info in `.json` metadata
  * Registry entry in DuckDB (`saved_reports`)
  * Fallback name = `temp_report` if user provides no name

---

### 5. `UploadAgent`

**Type**: `ConversableAgent`
**File**: `upload_agent.py`

**Purpose**: Metadata enrichment after file upload

**Behavior**:

* Called after `/upload` endpoint succeeds
* Prompts user:

  * What is this file?
  * Add notes, label, project ID
* Updates `.json` metadata for the file (via `save_metadata()`)
* Updates `doc_registry` for file type → description, usage context

---

### 6. `MemoryAgent`

**Type**: `ToolAgent`
**File**: `memory_agent.py`

**Purpose**: Fetch saved queries/reports

**Behavior**:

* Accepts lookup dict:

  ```json
  {
    "doc_id": "...",
    "query_name": "...",
    "tags": ["vendor"]
  }
  ```
* Searches DuckDB:

  * `saved_queries`
  * `saved_reports`
* Returns full SQL or report definition

---

## 📁 Project Structure Required

```
backend/
├── app.py                # Flask endpoints
├── chat_agent.py         # ChatAgent
├── orchestration_agent.py
├── query_agent.py
├── report_agent.py
├── memory_agent.py
├── upload_agent.py
├── agent_router.py       # route_request()
├── duckdb_manager.py     # db ops
├── duckdb_utils.py       # ensure tables
├── json_store.py         # JSON load/save
├── report_builder.py     # pandas + chart logic
└── excel_processor.py    # initial parsing
```

---

## 🛡️ Cursor Instructions

* All LLM prompts must be verifiable in code
* All file accesses must use explicit doc\_id paths
* Do not assume behavior from earlier sections
* Do not rename files or normalize filenames
* Do not compress logic — every function must be fully defined
* All agent input/output must be testable via mock dicts

---

## ✅ Testing Note

Agents must be tested with:

* input dict
* expected SQL or report object
* expected write to `.json`
* expected row in DuckDB

Tests should exist in `tests/agents/test_*.py`

---

Ready to build agents and config scaffolding.
