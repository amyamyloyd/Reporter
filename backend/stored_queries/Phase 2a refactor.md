# Refactor Instructions for Upload & JSON Metadata Pipeline

## Audience

Senior-level Python/JavaScript engineer using Cursor IDE. You are implementing changes to a FastAPI + React-based Excel reporting tool.

**DO NOT streamline, optimize, or refactor any logic beyond what is explicitly stated.** Follow the structure and instructions exactly as written. Your job is to implement the described behavior in a testable way, then test it, and only then allow the user to test.

---

## OVERVIEW

The goal is to bring the `/upload` endpoint and associated frontend/backend code into alignment with the documented product behavior. This includes:

* Using persistent DuckDB storage
* Standardizing table naming and metadata
* Improving the shape and fields of the saved JSON
* Preventing data duplication
* Preparing for agent reusability and recent uploads

---

## ✅ TASK 1: Use Persistent DuckDB Connection

### Goal

Switch from in-memory DuckDB to persistent database storage so data remains available across sessions.

### Current Behavior & Code

`duckdb.connect(':memory:')` is used inside `duckdb_manager.create_memory_database()`.

### Recommended Behavior

Use `duckdb.connect('excel_reporting.db')` for persistent storage.

### Location

* File: `backend/duckdb_manager.py`
* Function: `create_memory_database()` → rename to `create_persistent_database()`

### Instructions

* Rename the function for clarity.
* Replace the memory connection with a disk-based connection as specified.
* Ensure all calls to this function reflect the rename.

---

## ✅ TASK 2: Standardize DuckDB Table Naming

### Goal

Ensure table names follow the format: `<filename>_<document_type_code>_<YYYYMMDD>_<HHMMSS>`

### Current Behavior & Code

Table names are inconsistently generated (e.g. based on fragments of filenames or document type).

### Recommended Behavior

Generate table names using:

* Cleaned filename (no extension)
* Lowercase document type code
* Upload timestamp (derived from system time)

**Example**:

```
Campaign_data_campaign_20250901_080319
```

### Location

* File: `backend/app.py`, inside `/upload`
* File: `backend/duckdb_manager.py` when writing tables

### Instructions

* Create a function (either inline or in `utils.py`) to generate consistent table names.
* Replace all ad-hoc table name logic with calls to this function.

---

## ✅ TASK 3: Add Required JSON Metadata Fields

### Goal

Ensure saved JSON files include all fields needed for version control and agent logic.

### Current Behavior & Code

Some fields are included (`document_type`, `is_current_version`, etc), others are missing or inconsistently formatted.

### Recommended Behavior

Add these fields:

* `duckdb_table_name`
* `duckdb_loaded`
* `data_version` (from filename or fallback)
* `document_type_code` (short lowercase code)
* `is_current_version` (boolean)

### Location

* File: `backend/app.py`, inside `/upload` JSON write logic

### Instructions

* Extract these values during processing
* Add them to the output JSON dict
* Ensure proper types (e.g. boolean, string)

---

## ✅ TASK 4: Set `is_current_version` and Flip Older Files

### Goal

Mark the most recently uploaded document of each type as the current version. Older JSONs of the same type must be marked as not current.

### Current Behavior & Code

Every file is marked `is_current_version: true`, even if older files exist.

### Recommended Behavior

Before saving the new file:

* Search all existing JSON files for the same `document_type_code`
* For each match, load the JSON, set `is_current_version: false`, and resave
* Save the new file with `is_current_version: true`

### Location

* File: `backend/app.py`, inside `/upload`

### Instructions

* Use file I/O and JSON module to patch existing files
* Apply only to matching `document_type_code`

---

## ✅ TASK 5: Eliminate Duplicated Field Lists in JSON

### Goal

Prevent duplicate storage of field lists at both the root and sheet level.

### Current Behavior & Code

Root JSON includes `fields` and `normalized_fields`, which are also stored under each sheet.

### Recommended Behavior

* Remove root-level `fields` and `normalized_fields`
* Retain only `sheets.<sheet>.fields` and `normalized_fields`

### Location

* File: `backend/app.py`, inside `/upload`

### Instructions

* Update the structure of the output JSON accordingly
* Optionally add a single `normalized_fields_combined` if useful

---

## ✅ TASK 6: Return `json_filename` in Upload Response

### Goal

Ensure frontend components (especially `AgentChat.js`) can locate and reference the generated JSON.

### Current Behavior & Code

The JSON file is saved, but its name/path is not returned in the response.

### Recommended Behavior

Add a `json_filename` field to each file object in the response payload.

### Location

* File: `backend/app.py`, in `/upload` return statement

### Instructions

* Track each saved JSON’s filename
* Add it to the response object

---

## ✅ TASK 7: Fix Upload Bug – Pass Array to `uploadFiles()`

### Goal

Prevent frontend upload failure due to incorrect parameter type.

### Current Behavior & Code

FileUploader passes `FormData` to `uploadFiles()`, but that function internally creates its own `FormData`, expecting an array of files.

### Recommended Behavior

Pass the raw `File[]` array instead.

### Location

* File: `frontend/src/components/FileUploader.js`
* Line \~150, inside `performUpload`

### Instructions

Replace:

```js
uploadFiles(formData)
```

with:

```js
uploadFiles(validFiles)
```

---

## ✅ TASK 8: Store Uploads in `localStorage` as "Recent Uploads"

### Goal

Enable the frontend to display a list of recently uploaded files for the current session.

### Current Behavior & Code

No persistence of uploaded file metadata in the browser.

### Recommended Behavior

After successful upload, store result in `localStorage.recentUploads`

### Location

* File: `frontend/src/components/FileUploader.js`

### Instructions

```js
localStorage.setItem("recentUploads", JSON.stringify(result.files));
```

Later retrieval (optional):

```js
const recent = JSON.parse(localStorage.getItem("recentUploads") || "[]");
```

---

## ✅ TASK 9: Normalize `document_type_code`

### Goal

Use short lowercase type codes (`gl`, `campaign`, etc.) consistently across the app.

### Current Behavior & Code

Codes are inconsistent or missing.

### Recommended Behavior

Create a lookup table like:

```python
{
  "General Ledger": "gl",
  "Campaign Data": "campaign",
  "Vendor Reference": "vendor"
}
```

### Location

* File: `app.py` or helper module `document_type_utils.py`

### Instructions

* Apply this mapping after classifying the document
* Store both full name and short code in the JSON

---

## ✅ TASK 10: JSON Format Contract

### Goal

Ensure every JSON file has a consistent, valid structure as described.

### Recommended Format

```json
{
  "filename": "Campaign_data.xlsx",
  "json_filename": "Campaign_data_campaign_20250901_080319.json",
  "document_type": "Campaign Data",
  "document_type_code": "campaign",
  "data_version": "2025-09-01",
  "upload_timestamp": "2025-09-01_080319",
  "file_size": 15528,
  "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "sheets": {
    "Sheet1": {
      "fields": [...],
      "normalized_fields": [...],
      "field_mapping": {...},
      "types": {...},
      "row_count": 4
    }
  },
  "record_count": 4,
  "duckdb_table_name": "Campaign_data_campaign_20250901_080319",
  "duckdb_loaded": true,
  "is_current_version": true,
  "conversation_status": "completed",
  "ready_for_sql_agent": true
}
```

### Instructions

Match this structure exactly when saving the metadata JSON in `/upload`.

---

## 🔧 OPTIONAL TASK 11: Move Logic to `excel_processor.py`

### Goal

Move low-level Excel parsing operations (not business logic) out of `app.py` and into `excel_processor.py` to align with Phase 1 boundaries.

### Move These Functions:

* Field normalization (e.g. replace spaces, trim, convert to snake\_case)
* Data type inference (`object`, `float64`, `int64`, etc.)
* Field-to-normalized mapping dictionary construction

### Location

* Source: `backend/app.py`
* Target: `backend/excel_processor.py`

### Instructions

* Move the above logic only if it's being directly used to extract metadata
* DO NOT move DuckDB logic, agent logic, or file saving behavior
* Create helper functions like:

  * `normalize_fields(raw_headers: list[str]) -> list[str]`
  * `infer_types(df: pd.DataFrame) -> dict[str, str]`
  * `build_field_mapping(raw, normalized) -> dict`
* Update `/upload` to call these helpers

---

## 🔧 OPTIONAL TASK 12: Create `utils.py` for Shared Helpers

### Goal

Centralize reusable logic used across `app.py`, `file_analyzer.py`, and other modules.

### Create File

* Location: `backend/utils.py`

### Add These Functions:

* `generate_timestamp() -> str`  → returns `YYYYMMDD_HHMMSS`
* `parse_data_version(filename: str) -> str` → returns `YYYY-MM-DD`
* `build_table_name(filename: str, doc_type: str, timestamp: str) -> str`
* `normalize_field_name(field: str) -> str`

### Instructions

* Only create these if they are reused in multiple files
* DO NOT modify existing logic unless absolutely necessary to extract it
* Maintain 100% behavior parity

---

## ✅ TASK 13: Fix Document Classification Bug - Add LLM Classification Endpoint

### Goal

Fix the current bug where AgentChat asks for document type but doesn't use AI to automatically classify it from the user's description.

### Current Behavior & Code

When AgentChat asks "What type of document is this?" the agent requires manual document type selection instead of using AI classification.

### Recommended Behavior

Create a new backend endpoint `/classify-document` that:
1. Takes user description as input
2. Calls OpenAI 4.0 to analyze and classify the document
3. Returns structured response with document type, unique code, and description
4. Saves complete conversation history including LLM responses to JSON metadata

### Location

* File: `backend/app.py` - new endpoint
* File: `frontend/src/components/AgentChat.js` - update to call endpoint
* File: `backend/stored_queries/*.json` - update metadata structure

### Instructions

* Create `/classify-document` POST endpoint that accepts user description
* Use OpenAI API to determine document type from description
* Generate unique short codes (e.g., "WSR" for Weekly Sales Report)
* Return structured response with classification results
* Update AgentChat.js to call this endpoint
* Save conversation history with LLM responses to JSON
* Ensure document type codes are unique across all files

### Example Flow

1. User uploads file → Agent shows field analysis
2. Agent asks: "What type of document is this? Please describe its purpose"
3. User responds: "weekly sales report for tracking leads"
4. Frontend calls `/classify-document` with user description
5. LLM returns: `{"document_type": "Weekly Sales Report", "document_type_code": "WSR", "description": "Weekly sales report for tracking leads and performance metrics"}`
6. Agent confirms: "Great! So this is a Weekly Sales Report (WSR) - ready to query, create a report, or do you have another file to upload?"
7. Save to JSON metadata including conversation history and LLM response

---

## Final Instructions to Engineer

* Implement each change **exactly as described**
* **DO NOT** streamline, re-architect, or "clean up" anything not mentioned
* Write unit tests or logging checks to confirm new behaviors
* Only request user testing once your testing confirms accuracy
