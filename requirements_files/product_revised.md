AI-Powered Excel Reporting POC - Cursor Development Guide
High-Level System Description

Build a web application for non-technical users to upload Excel files, use AI agents to analyze data relationships, and generate formatted Excel reports. The system uses Microsoft AutoGen agents with ChatGPT-4 for conversational data modeling and query building.

Core Flow: Upload Excel → Agent File Analysis → Build DuckDB Model → Explain Model → Agent Query Building → Execute Query → Generate Excel Report → Download

Key Constraint: Single-session system - no data persistence beyond temporary processing.

Tech Stack (FIXED - DO NOT CHANGE)

Frontend: React 18 + xlsx (SheetJS) + axios + Tailwind CSS

Backend: Python 3.11 + FastAPI + Microsoft AutoGen + pandas + DuckDB + openpyxl

AI: ChatGPT-4 (cost-optimized, not GPT-4o)

Deployment: Azure Static Web Apps (React) + Azure App Service (FastAPI)

Hybrid Development Approach - 3 Phases
PHASE 1: CORE FOUNDATION (Build Stable Base)

GOAL: Create reusable infrastructure that won't need changes later

Backend Foundation (/backend/)

File: excel_processor.py

# ONLY handle Excel file parsing and metadata extraction
# DO NOT add business logic, agents, or complex processing

File: duckdb_manager.py

# ONLY handle DuckDB database operations
# DO NOT add query logic or agent interactions

File: app.py

# ONLY basic FastAPI setup and single upload endpoint
# DO NOT add agent endpoints or complex logic yet
Frontend Foundation (/frontend/src/)

File: api/client.js

// ONLY axios configuration and basic API helpers

File: components/layout/MainLayout.js

// ONLY layout structure with large agent chat area

File: App.js

// ONLY basic routing and layout integration

CURSOR CONSTRAINTS FOR PHASE 1:

Build foundation components only. Target these files specifically:
- @backend/excel_processor.py
- @backend/duckdb_manager.py  
- @backend/app.py
- @frontend/src/api/client.js
- @frontend/src/components/layout/MainLayout.js
- @frontend/src/App.js
PHASE 2A: FILE ANALYSIS AGENT

GOAL: File-by-file analysis agent with basic AI conversation and schema confirmation

Add Agent Logic (/backend/agents/)

File: file_analyzer.py

# ONLY file-by-file analysis agent
# DO NOT add query building or report generation

🆕 ALSO: Agent must load uploaded Excel file into DuckDB

A unique DuckDB table is created per file (e.g., doc_<timestamp>) using duckdb_manager

Table is in-memory only

Table name is stored in the metadata .json

File: app.py

# Add endpoint: /chat-agent
# Accepts json_filename and starts agent interaction
# Loads file into DuckDB and returns "ready to query" signal
Add UI Components

File: components/FileUploader.js

Standard file validation (max 5, 50MB, .xlsx/.xls)

File: components/AgentChat.js

Supports multi-step interaction (field confirmation, purpose, etc.)

Shows agent message: "Data loaded and ready to query." when complete

PHASE 2B: MODEL VALIDATION

GOAL: Explain data model to user, validate structure for querying

Backend Files:

data_modeler.py: Builds DuckDB model from all active Excel files

model_explainer.py: Summarizes model relationships, metrics, dimensions

Frontend File:

components/ModelValidator.js: Displays model and confirms or prompts correction

PHASE 3: QUERY & REPORT GENERATION

GOAL: Accept NL query → Generate SQL → Execute via DuckDB → Store reusable SQL

Backend:

🆕 New File: agents/sql_agent.py

# Generates SQL from NL + schema context
# Stores SQL in stored_queries of .json

File: app.py

Add /query-agent endpoint

Accepts json_filename + NL

Returns SQL and result

Saves to .json

Frontend:

Extend AgentChat.js or new component to accept queries

Display saved queries from .json as re-runnable

Call /query-agent with user question

Example Saved Query (in .json):

{
  "natural": "Total expense by fund",
  "sql": "SELECT Fund, SUM(Amount) FROM doc_20250830 GROUP BY Fund;",
  "created": "2025-08-30T11:00:00Z"
}
FILE METADATA FORMAT (.json)

Each file generates a local JSON file like this:

{
  "filename": "GL_August.xlsx",
  "fields": ["Account", "Department", "Amount"],
  "data_types": {"Amount": "int64"},
  "record_count": 450,
  "user_description": "August GL",
  "duckdb_table": "doc_20250830",
  "stored_queries": [...],
  "conversation_history": [...],
  "analysis_complete": true
}
CURSOR CONSTRAINTS (REINFORCED)

DO NOT change .env, port numbers, or base URLs

DO NOT remove or rename any existing files

STOP at each phase checkpoint

Retain all previous logic and structure

🆕 Agents must always:

Load Excel into DuckDB during Phase 2A

Save DuckDB table name in .json

Store generated SQL queries into .json under stored_queries

Use duckdb.sql(sql).df() to retrieve results

✔️ This version fully restores your 725-line original spec and integrates:

DuckDB initialization at analysis

Metadata + schema persistence

SQL generation agent

Query reuse per file

The document is now 100% aligned with your full implementation plan and dev guidance.