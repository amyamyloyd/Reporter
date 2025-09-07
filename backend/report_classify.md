# QueryAgent Excel Report Classification Implementation Plan

**Note (2025-09-06 13:45:00)**: This document was created while I was working excel exports which are different than reports. This is probably needed but we will probably dramatically rebuild this report agent when we build the modeling tool.

## Problem Statement

QueryAgent Excel exports (>65 records) currently only:
- Create Excel files and save to `stored_queries/excel_exports/`
- Save queries to `saved_queries` table with intelligent classification
- **MISSING**: No reports saved to `saved_reports` table with intelligent classification

## Current State Analysis

### ✅ Implemented
- `/reports` endpoint - intelligent classification
- ReportAgent - sophisticated intelligent classification
- QueryAgent queries - intelligent classification

### ❌ Missing
- QueryAgent Excel exports - no report classification

## Required Implementation

### 1. Import Required Functions
**File**: `backend/agents/query_agent.py`
- Add `save_report` to existing imports from `utils.duckdb_manager`
- Add `append_report_to_metadata` to existing imports from `utils.json_store`
- Import `time` module (already exists)

### 2. Create New Method
**File**: `backend/agents/query_agent.py`
- Create `async def _save_excel_as_report()` method
- Use **identical logic** to ReportAgent's `_save_report_automatically()`
- Same document type awareness, SQL uniqueness detection, LLM naming

### 3. Modify Excel Generation Flow
**File**: `backend/agents/query_agent.py`
- In `_determine_result_management()` when `strategy == "excel_download"`
- After `_generate_excel_file()` call
- Add `await self._save_excel_as_report()` call

### 4. Make Method Async
**File**: `backend/agents/query_agent.py`
- Change `_determine_result_management()` to `async def`
- Update call in `process_query_request()` to use `await`

## Implementation Details

### Report Data Structure
```python
report_data = {
    "report_name": report_name,  # LLM-generated or temp
    "sql": sql_query,  # Reconstructed from query context
    "filters": {},  # Empty for Excel exports
    "group_by": [],  # Empty for Excel exports
    "format": "excel",
    "chart": "",
    "output_type": "xlsx",
    "excel_file": excel_file.get("filename", ""),
    "summary": f"Excel export with {len(rows)} records",
    "timestamp": excel_file.get("timestamp", ""),
    "auto_saved": True
}
```

### Classification Logic
- Use same `check_sql_uniqueness()` function
- Use same `generate_report_name_with_llm()` function
- Same document type awareness
- Same global vs local storage strategy
- Add `excel_export` tag to distinguish from regular reports

### SQL Query Reconstruction
- Need to reconstruct the SQL that generated the Excel
- Use document metadata to get table name
- Create basic `SELECT * FROM table_name LIMIT 1000` query
- This ensures SQL uniqueness detection works properly

## Key Benefits

- **Consistent classification** across all report sources
- **Professional LLM names** for Excel exports
- **Uniqueness detection** prevents duplicate reports
- **Document type awareness** enables cross-document reuse
- **JSON metadata** includes Excel file information

## Files to Modify

1. `backend/agents/query_agent.py` - Main changes
2. No other files need modification

## Testing Strategy

- Test with query returning >65 records
- Verify Excel file creation
- Verify report saved to `saved_reports` table
- Verify JSON metadata updated
- Verify LLM-generated report name

## Success Criteria

- QueryAgent Excel exports get same intelligent classification as ReportAgent
- Reports saved to `saved_reports` table with proper classification
- JSON metadata includes Excel file information
- LLM generates professional report names
- SQL uniqueness detection works properly

## Notes

- This ensures QueryAgent Excel exports get the same intelligent classification as ReportAgent and `/reports` endpoint
- Follows exact same pattern as existing ReportAgent implementation
- Maintains consistency across all report sources

