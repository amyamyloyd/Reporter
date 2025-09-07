# 🧠 SuperMenu Implementation Plan for Cursor AI (Q\&A Kickoff)

This document outlines a phased, zero-shot-friendly implementation plan for the **SuperMenu**, integrating metadata-driven navigation of saved queries, reports, and modeling datasets. This plan uses existing endpoints and agent logic and is designed to be compatible with `AutoGenChat.js`, `query_agent.py`, and `report_builder.py`.

---

## 🧱 Core Tabs Overview

### Tab 1: **All**

* Displays **all saved queries, reports, and Excel exports**.
* Grouped by `document_type` (not doc\_type\_code).
* **Multi-select dropdown** allows filtering by one or more `document_type`s.
* Entries are shown in groups of **5**, with a **"More..." button** loading 5 more entries per click.
* If the list exceeds 30 items, switch to a **scrollable modal popup** with search and filter.
* **Visual Highlighting:**

  * If `is_current_version: true`, highlight the entry visually:

    * Use **bold text**, **green check icon**, or **light-green background**.
* **Usage Indicators:**

  * Queries: show `use_count` as a badge or number.
  * Reports: show `generation_count` similarly.
* Sorting Options:

  * Default sort: `last_used desc` (queries), `last_generated desc` (reports).
  * Allow column header click to sort.
* **Favorites Support (MVP):**

  * Each entry shows a **clickable star icon** to toggle `is_favorite`.
  * Favorites are saved via:

    * `PATCH /query/:id` → `{ is_favorite: true|false }`
    * `PATCH /report/:id` → `{ is_favorite: true|false }`
  * Starred items persist and are highlighted visually (e.g., filled star icon).
  * Include **"Show Favorites Only"** toggle for this tab, filters down to favorite items only.
  * **Persistence:** `is_favorite` is stored in **DuckDB** as a column in the metadata tables. If not present, Cursor must add `is_favorite` to the schema via `ALTER TABLE` and update writes accordingly.

### Tab 2: **Context**

* Filters saved queries/reports based on document types **present in `localStorage.recentUploads`**.
* Shows a **dropdown filter** of document types found in uploaded docs.
* Uses the same expandable UI, sorting, usage counters, and highlighting as Tab 1.
* Shows full history (not just current version), but highlights current version entries as in Tab 1.
* Honors "Show Favorites Only" filter and favorite stars.

### Tab 3: **Model**

* Displays **uploaded files from `localStorage.recentUploads`**, showing:

  * `filename` (original file name)
  * associated `json_filename`
  * associated DuckDB table name (parsed from JSON)
* User selects which files to include in a modeling session.
* On submission, this payload will be passed to the future `data_model_agent`:

```json
{
  "selected_datasets": [
    {
      "filename": "HospitalA.xlsx",
      "json_filename": "HospitalA_ham_20250906_194959.json",
      "duckdb_table": "HospitalA_ham_20250906_194959"
    }
  ]
}
```

Agent is expected to retrieve full field list and metadata from `json_filename`. Intended actions like `join`, `aggregate`, and `compare_periods` are anticipated.

---

## ✅ Phase 1: Foundational UI Scaffolding

### Goal: Establish menu tabs, expanders, and basic display logic for all metadata types.

### Components/Files:

* `MainLayout.js`: Add tab UI with `ALL`, `CONTEXT`, and `MODEL` tabs.
* `QueryListSection.js` (new): Reusable renderer for queries/reports/exports by type.
* `FileModelSelector.js` (new): Renders uploaded files for selection.

### Tasks:

* Create 3 tab views (with Tailwind or AdminLTE components).
* Fetch metadata via `GET /queries`, `GET /reports`, and group by `document_type`.
* For each metadata card:

  * Render name, usage count, type, and version status.
  * Show 5 per group by default.
  * Add "More..." button.
  * Use conditional styling for `is_current_version` (bold text, green background, check icon).
  * Include **favorite star icon** per item, toggle with click and persist.
  * Add tab-wide toggle for "Show Favorites Only".
* Do not include action buttons yet.

---

## ✅ Phase 2: Click-to-Run Queries & Reports (MVP)

### Goal: When a user clicks an item, it executes the query/report and uses existing formatting logic for result display/download.

### Actions on Click:

* For **queries**:

  * Call `POST /query/run` with full saved object (schema + SQL).
  * Backend uses DuckDB to execute the SQL. This bypasses LLM and ensures deterministic results.

* For **reports**:

  * Call `POST /report/run` with full saved report config.
  * Backend runs report builder logic directly.

### Result Display:

* If result ≤65 rows → HTML table sent to frontend (`AutoGenChat.js`) and displayed inline.
* If >65 rows → triggers Excel download via `/stored_queries/excel_exports/…`.

### Files:

* `AutoGenChat.js`: Accept `queryResult` or `reportResult` injected via props or global state.
* `query_agent.py`: add `@app.post('/query/run')` endpoint to execute raw SQL.
* `report_builder.py`: add `@app.post('/report/run')` endpoint to execute report config.

---

## ✅ Phase 3: MVP Enhancements (Still Core)

### Features:

* ⭐️ **Favorites (ALREADY MVP):**

  * Included in Phase 1 and Phase 2 scope.
  * **Toggle icon, backend persistence, and filtering all required.**
  * Field must exist in **DuckDB** table.
  * If not yet created, use `ALTER TABLE` to add `is_favorite BOOLEAN DEFAULT false`.

* 📄 **Version Management (visual only):**

  * Display `Uploaded: date` + `Version: X` in light gray text.
  * Highlight `is_current_version: true` with:

    * Bold text
    * Light-green background
    * ✅ checkmark or tag

* 💬 **Prompt-to-Run (Future Alpha Feature):**

  * In chat box, user can type: `run <<query_name>>`
  * `AutoGenChat.js` detects command and pulls query by name.
  * Executes via `/query/run` using full schema.
  * Result uses existing formatting logic.

* 🏷️ **Tag Discovery Filters (Future Alpha Feature):**

  * Pill filters at top of ALL tab for tags.
  * Enables discovery and organization.

---

## 🧠 Metadata Reference (Saved Items)

```ts
Query:
{
  id: string,
  query_name: string,
  document_type: string,
  is_current_version: boolean,
  is_global: boolean,
  is_favorite: boolean,
  use_count: number,
  schema: string[],
  tags: string[],
  last_used: ISODate,
}

Report:
{
  id: string,
  report_name: string,
  document_type: string,
  is_current_version: boolean,
  is_global: boolean,
  is_favorite: boolean,
  generation_count: number,
  last_generated: ISODate,
}
```

---

## 🔁 Supporting Endpoints (Required)

* `POST /query/run` → executes saved query directly using SQL
* `POST /report/run` → executes saved report directly using config
* `GET /queries`, `GET /reports` → returns all saved items
* `PATCH /query/:id`, `PATCH /report/:id` → toggle favorite (must be implemented)
* `/tables` → advanced display view (optional)

---

## 🔧 Result Formatting Logic (Already Integrated)

* `query_agent.py`

  * `_determine_result_management()` → chooses HTML vs. Excel
  * `_generate_excel_file()`
  * `_generate_excel_filename_with_llm()`

* `report_builder.py`

  * `build_report()` → entry point
  * `generate_html_report()`
  * `generate_xlsx_report()`
  * `generate_json_report()`

* `AutoGenChat.js`

  * Renders HTML tables (`lines 424–452`)
  * Adds Excel download buttons (`lines 454–466`)

---

## 🧠 Design Notes

* Do NOT include upload prompts in any tab.
* Do NOT filter out historical versions — just **visually highlight** `is_current_version: true`.
* Do NOT include RBAC for POC.
* Do NOT mutate localStorage manually.
* Do NOT change formatting logic — re-use result renderers from `/query` and `/report` logic.

---

## ✅ Final Summary

The SuperMenu enables:

* Launching sessions without needing file upload first
* Surfacing full catalog of saved logic
* Executing saved queries/reports with uniform formatting
* Supporting favorites (star + filter), version indicators, and data model selection

Each phase is testable and can be committed incrementally. Ready for implementation.

---

## 🔍 Developer Review Q\&A: Architecture Clarifications

### 1. Backend Endpoint Gaps

* **PATCH endpoints for favorites** do not yet exist. These must be implemented in the backend for both queries and reports.
* **GET /queries and GET /reports** return full metadata records as shown in the Metadata Reference section above.

### 2. localStorage Structure Ambiguity

* `localStorage.recentUploads` contains an array of uploaded file metadata objects, typically like:

```json
[
  {
    "filename": "HospitalA.xlsx",
    "json_filename": "HospitalA_ham_20250906_194959.json",
    "duckdb_table": "HospitalA_ham_20250906_194959"
  }
]
```

* This structure informs the MODEL tab and drives context filters.

### 3. Component Architecture Questions

* `MainLayout.js` owns tab routing and passes state to tab components.
* `QueryListSection.js` and `FileModelSelector.js` are self-contained renderers, passed metadata as props.
* Global state is minimal; props or Context API may be used if shared state emerges.

### 4. Data Flow Confusion

* Menu components emit events on click (`onRunItem(item)`), passed up to `MainLayout`.
* `MainLayout.handleRunItem(item)` calls `/query/run` or `/report/run` and forwards the result to `AutoGenChat.js` via prop injection or message bus.

### 5. Excel Export Integration

* For large results, the backend generates an Excel file saved in `/stored_queries/excel_exports/`.
* The response contains a download URL or triggers redirect. Excel files are stored temporarily by backend logic.

### 6. Version Management Details

* Version is read-only and comes from the metadata object: `Version: X`, `is_current_version: true`.
* It is not calculated on the fly; it is stored per save.

### 7. Modal Implementation

* Modal is triggered after "More..." reveals >30 items in a group.
* Use Bootstrap or AdminLTE modal component.
* Scrollable, filterable modal shows remaining items with search input.

### 8. Backend Dependencies

* `query_agent.py` must add `/query/run` to bypass LLM and use raw SQL.
* `report_builder.py` must add `/report/run` to run saved report config.
* Payload to these endpoints is the full saved object (no ID re-fetching).
