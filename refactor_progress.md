# Phase 2a Refactor Progress Tracker

## Overview
This document tracks the systematic refactoring of the Excel reporting POC according to the Phase 2a specifications. Each task will be implemented, tested, and committed before moving to the next.

## Task Status Legend
- 🔴 **NOT STARTED** - Task not yet begun
- 🟡 **IN PROGRESS** - Task currently being worked on
- 🟢 **COMPLETED** - Task finished, tested, and committed
- ❌ **BLOCKED** - Task blocked by dependencies or issues

---

## ✅ TASK 1: Use Persistent DuckDB Connection
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Rename `create_memory_database()` to `create_persistent_database()` in `duckdb_manager.py`
- [ ] Change connection from `:memory:` to `excel_reporting.db`
- [ ] Update all function calls to use new name
- [ ] Test persistent storage across sessions
- [ ] Commit changes

### Files to modify:
- `backend/duckdb_manager.py`

---

## ✅ TASK 2: Standardize DuckDB Table Naming
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Create table naming function (inline or in utils.py)
- [ ] Implement format: `<filename>_<document_type_code>_<YYYYMMDD>_<HHMMSS>`
- [ ] Update `/upload` endpoint in `app.py`
- [ ] Update table creation in `duckdb_manager.py`
- [ ] Test table naming consistency
- [ ] Commit changes

### Files to modify:
- `backend/app.py`
- `backend/duckdb_manager.py`
- `backend/utils.py` (if created)

---

## ✅ TASK 3: Add Required JSON Metadata Fields
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Add `duckdb_table_name` field
- [ ] Add `duckdb_loaded` field
- [ ] Add `data_version` field (from filename or fallback)
- [ ] Add `document_type_code` field (short lowercase code)
- [ ] Ensure `is_current_version` field exists
- [ ] Test JSON structure validation
- [ ] Commit changes

### Files to modify:
- `backend/app.py`

---

## ✅ TASK 4: Set `is_current_version` and Flip Older Files
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Search existing JSON files for same `document_type_code`
- [ ] Load and update older files to set `is_current_version: false`
- [ ] Save new file with `is_current_version: true`
- [ ] Test version flipping logic
- [ ] Commit changes

### Files to modify:
- `backend/app.py`

---

## ✅ TASK 5: Eliminate Duplicated Field Lists in JSON
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Remove root-level `fields` array
- [ ] Remove root-level `normalized_fields` array
- [ ] Keep only sheet-level field information
- [ ] Optionally add `normalized_fields_combined` if useful
- [ ] Test JSON structure consistency
- [ ] Commit changes

### Files to modify:
- `backend/app.py`

---

## ✅ TASK 6: Return `json_filename` in Upload Response
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Track saved JSON filename during processing
- [ ] Add `json_filename` to response payload
- [ ] Test frontend can access the filename
- [ ] Commit changes

### Files to modify:
- `backend/app.py`

---

## ✅ TASK 7: Fix Upload Bug – Pass Array to `uploadFiles()`
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Identify incorrect `FormData` usage in `FileUploader.js`
- [ ] Change to pass raw `File[]` array instead
- [ ] Test file upload functionality
- [ ] Commit changes

### Files to modify:
- `frontend/src/components/FileUploader.js`

---

## ✅ TASK 8: Store Uploads in `localStorage` as "Recent Uploads"
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Add localStorage storage after successful upload
- [ ] Store in `localStorage.recentUploads`
- [ ] Test persistence across browser sessions
- [ ] Commit changes

### Files to modify:
- `frontend/src/components/FileUploader.js`

---

## ✅ TASK 9: Normalize `document_type_code`
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Create document type lookup table
- [ ] Map full names to short lowercase codes
- [ ] Apply mapping after document classification
- [ ] Store both full name and short code in JSON
- [ ] Test code consistency
- [ ] Commit changes

### Files to modify:
- `backend/app.py` or `backend/document_type_utils.py`

---

## ✅ TASK 10: JSON Format Contract
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Ensure consistent JSON structure as specified
- [ ] Validate all required fields are present
- [ ] Test JSON schema compliance
- [ ] Commit changes

### Files to modify:
- `backend/app.py`

---

## 🔧 OPTIONAL TASK 11: Move Logic to `excel_processor.py`
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Move field normalization logic
- [ ] Move data type inference logic
- [ ] Move field mapping construction
- [ ] Update `/upload` to call helpers
- [ ] Test functionality preservation
- [ ] Commit changes

### Files to modify:
- `backend/app.py`
- `backend/excel_processor.py`

---

## 🔧 OPTIONAL TASK 12: Create `utils.py` for Shared Helpers
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Create `backend/utils.py` file
- [ ] Add `generate_timestamp()` function
- [ ] Add `parse_data_version()` function
- [ ] Add `build_table_name()` function
- [ ] Add `normalize_field_name()` function
- [ ] Test utility functions
- [ ] Commit changes

### Files to modify:
- `backend/utils.py` (new file)

---

## Testing Strategy
Each task will be tested individually before moving to the next:
1. **Unit Testing** - Test specific functionality
2. **Integration Testing** - Test with related components
3. **End-to-End Testing** - Test complete upload flow
4. **Code Review** - Ensure 30% comment ratio and best practices

## Commit Strategy
- Each completed task gets its own commit
- Commit messages follow format: `feat: [Task X] Description of changes`
- Always test before committing
- Keep commits focused and atomic

## ✅ TASK 13: Fix Document Classification Bug - Add LLM Classification Endpoint
**Status:** 🟡 IN PROGRESS

### Sub-steps:
- [x] Create new backend endpoint `/classify-document` for LLM classification
- [x] Endpoint takes user description and returns AI-determined document type, code, and description
- [x] Ensure unique document type codes across all files
- [x] Update AgentChat.js to call this endpoint instead of manual classification
- [x] Save complete conversation history to JSON metadata including LLM responses
- [ ] Test classification flow end-to-end
- [ ] Commit changes

### Files to modify:
- `backend/app.py` (new endpoint)
- `frontend/src/components/AgentChat.js`
- `backend/stored_queries/*.json` (metadata structure)

### Bug Description:
Currently, when AgentChat asks "What type of document is this?" the agent doesn't use AI to automatically classify the document type from the user's description. Instead, it requires manual selection. The fix should:
1. Call LLM (OpenAI 4.0) to analyze user description
2. Automatically determine document type (e.g., "Weekly Sales Report" from "weekly sales report for tracking leads")
3. Generate unique short code (e.g., "WSR")
4. Save complete conversation history with LLM responses
5. Allow future uploads of same type to inherit the classification

---

## Current Focus
**Next Task:** TASK 1 - Use Persistent DuckDB Connection

---

*Last Updated: 2025-09-01*
*Total Tasks: 13*
*Completed: 0*
*In Progress: 1*
*Remaining: 12*
