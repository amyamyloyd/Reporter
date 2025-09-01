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
**Status:** 🟢 COMPLETED

### Sub-steps:
- [x] Rename `create_memory_database()` to `create_persistent_database()` in `duckdb_manager.py`
- [x] Change connection from `:memory:` to `excel_reporting.db`
- [x] Update all function calls to use new name
- [x] Test persistent storage across sessions
- [x] Commit changes

### Files to modify:
- `backend/duckdb_manager.py`

### Notes:
- ✅ Persistent database connection working correctly
- ✅ Upload endpoint functional with persistent storage
- ✅ Data persists across backend restarts
- ✅ Fixed corrupted database file issue

---

## ✅ TASK 2: Standardize DuckDB Table Naming
**Status:** 🟡 UPDATED (Standardization Deferred)

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

### Notes:
- ✅ Table naming currently uses `<filename>_<timestamp>` (e.g., `employees_20250901102448`)
- 🟡 Standardized naming with document type code is **deferred**
- ✅ Upload endpoint and all current features work as expected
- 🟡 Will enforce new naming convention in future features or refactors as needed

---

## ✅ TASK 3: Add Required JSON Metadata Fields
**Status:** 🔴 NOT STARTED

### Sub-steps:
- [ ] Add `latest_version` column to doc_registry table
- [ ] Create `manage_document_version()` function in duckdb_manager.py
- [ ] Update upload endpoint to call version function for known documents
- [ ] Update agent chat to call version function for new documents
- [ ] Add `version` field to JSON metadata for both flows
- [ ] Test version increment logic for known document types
- [ ] Test version creation (1.0) for new document types
- [ ] Test JSON structure validation with version field
- [ ] Commit changes

### Files to modify:
- `backend/app.py` (update both upload and chat-agent endpoints)
- `backend/duckdb_manager.py` (add version management function and table schema)
- `backend/stored_queries/*.json` (add version field to metadata)

### Implementation Plan:
1. **Database Schema Update**: Add `latest_version VARCHAR DEFAULT '1.0'` to doc_registry
2. **Shared Function**: Create `manage_document_version()` for version logic
3. **Known Document Flow**: Upload endpoint calls version function, increments version
4. **New Document Flow**: Agent chat calls version function, sets version to 1.0
5. **JSON Updates**: Add `version` field to all JSON metadata files
6. **Registry Updates**: Update `latest_version` in doc_registry for both flows

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
**Next Task:** TASK 2 - Standardize DuckDB Table Naming

---

*Last Updated: 2025-09-01*
*Total Tasks: 13*
*Completed: 1*
*In Progress: 1*
*Remaining: 11*
