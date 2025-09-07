# Implementation Plan: Enhanced Excel Export Naming & Persistence

## Overview
Transform the QueryAgent's Excel export system to use LLM-generated semantic filenames, ensure URL encoding compatibility, and persist export metadata in document JSON.

## Phase 1: LLM Filename Generation Enhancement

### 1.1 Modify `generate_query_name_with_llm()` Function
**Location**: `backend/app.py` (existing function)

**Enhancement Requirements**:
- Add filename generation mode to existing function
- Create specialized prompt for Excel export naming
- Ensure URL-safe character set compliance
- Include timestamp in LLM-generated name

**New Function Signature**:
```python
async def generate_query_name_with_llm(sql: str, query_text: str, document_type: str, 
                                     document_type_code: str, 
                                     export_type: str = "query") -> Dict[str, Any]
```

**LLM Prompt Instructions**:
```
Generate a concise, URL-safe filename for Excel export with these requirements:
1. NO spaces, special characters, or symbols (only alphanumeric, hyphens, underscores)
2. Keep under 45 characters (before timestamp)
3. Use underscores for word separation
4. Make it descriptive of the query purpose
5. Include timestamp in format: YYYYMMDD_HHMMSS
6. End with .xlsx extension
7. Examples: "costcenter_central_supply_20250905_191025.xlsx", "vendors_chicago_20250905_191030.xlsx"
```

### 1.2 Create Filename Validation Function
**Location**: `backend/utils/filename_validator.py` (new file)

**Purpose**: Validate LLM-generated filenames meet requirements
- Check URL-safe character compliance
- Verify length constraints
- Ensure .xlsx extension
- Test URL encoding compatibility

## Phase 2: QueryAgent Excel Generation Enhancement

### 2.1 Modify `_generate_excel_file()` Method
**Location**: `backend/agents/query_agent.py` lines 373-424

**Changes Required**:
- Replace simple truncation with LLM-generated naming
- Integrate with enhanced `generate_query_name_with_llm()`
- Add filename validation
- Generate proper download URL
- Return enhanced metadata structure

**New Flow**:
1. Call LLM for semantic filename generation
2. Validate filename meets requirements
3. Create file with LLM-generated name
4. Generate download URL
5. Return comprehensive metadata

### 2.2 Enhance Result Management
**Location**: `backend/agents/query_agent.py` lines 332-371

**Updates**:
- Pass additional context to filename generation
- Include document metadata for better LLM context
- Handle filename generation failures gracefully

## Phase 3: Data Persistence Enhancement

### 3.1 Enhance JSON Metadata Storage
**Location**: `backend/utils/json_store.py` (existing `append_query_to_metadata()`)

**New Structure**:
```python
query_data = {
    "query_name": query_name,
    "query_text": query_text,
    "sql": sql_query,
    "summary": query_result.get("summary", ""),
    "timestamp": query_result.get("execution_time", ""),
    "auto_saved": True,
    "excel_export": {
        "filename": "costcenter_central_supply_20250905_191025.xlsx",
        "download_url": "/download-excel/costcenter_central_supply_20250905_191025.xlsx",
        "filepath": "stored_queries/excel_exports/costcenter_central_supply_20250905_191025.xlsx",
        "row_count": 150,
        "column_count": 8,
        "generated_at": "2025-09-05T19:10:25Z",
        "file_size_bytes": 245760,
        "export_type": "query_results"
    }
}
```

### 3.2 Update `_save_query_automatically()` Method
**Location**: `backend/agents/query_agent.py` lines 753-870

**Enhancements**:
- Include Excel export metadata in JSON storage
- Ensure download URL is properly formatted
- Add error handling for metadata persistence failures

## Phase 4: URL Encoding & Download Enhancement

### 4.1 Enhance FastAPI Download Endpoint
**Location**: `backend/app.py` lines 1637-1663

**Improvements**:
- Add proper URL decoding for complex filenames
- Enhance security validation
- Improve error handling and logging
- Add download tracking

**New Endpoint Features**:
- Handle both old and new filename formats
- Proper MIME type detection
- Security validation for all filename patterns
- Comprehensive error responses

### 4.2 Add URL Encoding Utilities
**Location**: `backend/utils/url_utils.py` (new file)

**Functions**:
- `encode_filename_for_url(filename: str) -> str`
- `decode_url_to_filename(encoded_filename: str) -> str`
- `validate_url_safe_filename(filename: str) -> bool`

## Phase 5: Error Handling & Fallback Strategy

### 5.1 Filename Generation Fallbacks
**Priority Order**:
1. LLM-generated semantic name
2. Simple pattern-based name (if LLM fails)
3. Timestamp-only name (if all else fails)

**Fallback Examples**:
- LLM fails → `query_export_20250905_191025.xlsx`
- Complete failure → `export_20250905_191025.xlsx`

### 5.2 Comprehensive Error Handling
**Areas to Cover**:
- LLM API failures
- Filename validation failures
- File system write errors
- URL encoding issues
- JSON persistence failures

## Phase 6: Testing & Validation

### 6.1 Unit Tests
**Test Files to Create/Update**:
- `test_filename_generation.py`
- `test_url_encoding.py`
- `test_excel_export_persistence.py`

**Test Scenarios**:
- LLM filename generation with various query types
- URL encoding/decoding round-trip tests
- File system operations with different filename patterns
- JSON metadata persistence validation

### 6.2 Integration Tests
**Test Scenarios**:
- End-to-end query to Excel export flow
- Download link functionality
- Metadata persistence across sessions
- Error handling and fallback mechanisms

## Implementation Timeline

### Week 1: Core LLM Integration
- Enhance `generate_query_name_with_llm()` function
- Create filename validation utilities
- Update `_generate_excel_file()` method

### Week 2: Data Persistence
- Enhance JSON metadata storage
- Update `_save_query_automatically()` method
- Add comprehensive error handling

### Week 3: URL & Download Enhancement
- Enhance FastAPI download endpoint
- Add URL encoding utilities
- Implement fallback strategies

### Week 4: Testing & Validation
- Comprehensive unit and integration tests
- Performance testing with large datasets

## Success Criteria

### Functional Requirements
✅ **LLM-generated semantic filenames** (no spaces, URL-safe)
✅ **Proper URL encoding** for download links
✅ **Excel export metadata persistence** in document JSON
✅ **Comprehensive error handling** with fallbacks

### Technical Requirements
✅ **URL-safe character set** compliance
✅ **Filename length constraints** (45 chars + timestamp)
✅ **Proper MIME type handling** for downloads
✅ **Security validation** for all filename patterns
✅ **Comprehensive logging** for debugging

### Performance Requirements
✅ **Sub-second filename generation** via LLM
✅ **Efficient file system operations**
✅ **Minimal impact** on query processing time
✅ **Reliable download link generation**

This implementation plan ensures a robust, scalable solution that addresses all the identified issues while maintaining system reliability and user experience.
