# DuckDB Integration - /upload Endpoint Update

## **OBJECTIVE**
Update the existing `/upload` endpoint in `app.py` to **additionally** create DuckDB tables when JSON files are created. This is a **discrete change only** - no other modifications to existing functionality.

## **CURRENT BEHAVIOR (KEEP AS-IS)**
- `/upload` creates JSON metadata files
- `/upload` saves Excel files to disk
- `/upload` returns file information to frontend
- All existing functionality remains unchanged

## **NEW BEHAVIOR (ADD ONLY)**
After the JSON file is created, **additionally**:

1. **Load Excel data into DuckDB**
   - Read the saved Excel file from disk
   - Use pandas to load into DataFrame
   - Create DuckDB table using `duckdb_manager.dataframe_to_table()`

2. **Update JSON metadata**
   - Add `duckdb_table_name` field to JSON
   - Add `duckdb_loaded` boolean field
   - Add `data_version` field (extracted from filename)
   - Add `document_type` field (GL, Vendor, Campaign, etc.)
   - Add `is_current_version` boolean field

3. **Persistent DuckDB storage**
   - Use `duckdb.connect('excel_reporting.db')` instead of `:memory:`
   - Data persists between user sessions

## **DOCUMENT TYPE RECOGNITION**

### **Purpose**
Enable natural language queries like:
- "Show me the latest GL data"
- "What's in the most recent vendor reference file?"
- "Compare current vs. previous campaign data"

### **Document Type Detection**
The system should recognize document types from:
1. **Filename patterns** (e.g., "GL_", "Vendor_", "Campaign_")
2. **User input** during upload process
3. **Content analysis** (column patterns, data types)

### **Document Type Examples**
- **GL** (General Ledger): Financial transactions, account codes
- **Vendor** (Reference): Vendor codes, names, contact info
- **Campaign** (Marketing): Campaign data, metrics, ROI
- **Inventory** (Operational): Stock levels, product codes
- **Employee** (HR): Staff data, departments, roles

## **ENHANCED TABLE NAMING CONVENTION**

### **Format**: `{type}_{timestamp}_{version}`
- **Type**: Document type abbreviation (gl, vendor, campaign, etc.)
- **Timestamp**: Date in YYYYMMDD format
- **Version**: Time in HHMMSS format

### **Examples**:
- `gl_20250827_160349` (General Ledger from Aug 27, 2025 at 16:03:49)
- `vendor_20250829_103600` (Vendor reference from Aug 29, 2025 at 10:36:00)
- `campaign_20250827_205016` (Campaign data from Aug 27, 2025 at 20:50:16)

### **Benefits**:
- **Natural Language Queries**: "latest GL data" → `gl_*` tables
- **Version Tracking**: Multiple uploads of same document type
- **Easy Filtering**: `SELECT * FROM information_schema.tables WHERE table_name LIKE 'gl_%'`
- **Time-based Analysis**: Compare data across different time periods

## **UPDATED JSON STRUCTURE**

### **New Fields Added**:
```json
{
  "duckdb_table_name": "gl_20250827_160349",
  "duckdb_loaded": true,
  "data_version": "2025-08-27",
  "document_type": "GL",
  "document_type_code": "gl",
  "is_current_version": true,
  "existing_fields": ["filename", "fields", "record_count", ...]
}
```

### **Document Type Field**:
- **`document_type`**: Human-readable name (e.g., "General Ledger")
- **`document_type_code`**: Short code for queries (e.g., "gl")
- **`is_current_version`**: Boolean indicating if this is the latest version

## **NATURAL LANGUAGE QUERY SUPPORT**

### **Query Examples**:
```sql
-- Get latest GL data
SELECT table_name FROM information_schema.tables 
WHERE table_name LIKE 'gl_%' 
ORDER BY table_name DESC LIMIT 1;

-- Get all vendor reference tables
SELECT table_name FROM information_schema.tables 
WHERE table_name LIKE 'vendor_%';

-- Compare current vs. previous GL data
SELECT table_name FROM information_schema.tables 
WHERE table_name LIKE 'gl_%' 
ORDER BY table_name DESC LIMIT 2;
```

### **Agent Integration**:
When user asks "Show me the latest GL data", the agent will:
1. Query `information_schema.tables` for `gl_*` tables
2. Order by table name (newest first)
3. Use the most recent table for analysis

## **IMPLEMENTATION REQUIREMENTS**

### **File Changes (ONLY these files)**
- `backend/app.py` - Update `/upload` endpoint
- `backend/duckdb_manager.py` - Ensure `dataframe_to_table()` works with persistent connection

### **New Functions Needed**:
- **Document Type Detection**: Analyze filename/content to determine type
- **Table Naming**: Generate consistent table names
- **Version Management**: Track current vs. historical versions

## **DATA VERSION IDENTIFICATION**

### **Current Method (Filename-based)**
- Extract date/time from filename timestamp
- Use as `data_version` field
- Example: `GL_2025-08-27_160349.xlsx` → `"2025-08-27"`

### **Future Enhancement (Agent-based)**
- Agent asks user: "What type of document is this?"
- User responds: "General Ledger" or "Vendor reference"
- Store user's description as `document_type`

## **VERIFICATION REQUIREMENTS**

### **After Upload, Verify**:
1. **JSON file exists** with all fields including DuckDB metadata
2. **DuckDB table exists** and contains all Excel data
3. **Row count matches** between Excel file and DuckDB table
4. **Data accessible** via DuckDB queries
5. **Document type correctly identified** and stored
6. **Table naming follows convention** (type_timestamp_version)

### **Test Queries**:
```sql
-- List all tables by type
SELECT 
  CASE 
    WHEN table_name LIKE 'gl_%' THEN 'General Ledger'
    WHEN table_name LIKE 'vendor_%' THEN 'Vendor Reference'
    WHEN table_name LIKE 'campaign_%' THEN 'Campaign Data'
    ELSE 'Other'
  END as document_type,
  table_name,
  COUNT(*) as table_count
FROM information_schema.tables 
WHERE table_schema = 'main'
GROUP BY document_type, table_name;

-- Get latest version of each document type
SELECT 
  SUBSTR(table_name, 1, INSTR(table_name, '_') - 1) as doc_type,
  MAX(table_name) as latest_table
FROM information_schema.tables 
WHERE table_schema = 'main'
GROUP BY doc_type;
```

## **CONSTRAINTS**

### **DO NOT CHANGE**:
- Existing JSON creation logic
- Existing Excel file saving
- Existing frontend response format
- Any other endpoints or functionality
- File naming conventions
- Error handling patterns

### **ONLY ADD**:
- DuckDB table creation
- DuckDB metadata to JSON
- Document type recognition
- Enhanced table naming
- Persistent database connection

## **SUCCESS CRITERIA**

1. **User uploads Excel file**
2. **JSON created** (existing behavior)
3. **Excel saved** (existing behavior)  
4. **Document type detected** (NEW)
5. **DuckDB table created** with proper naming (NEW)
6. **JSON updated** with DuckDB metadata (NEW)
7. **Data persists** between sessions (NEW)
8. **Natural language queries work** (NEW)
9. **All existing functionality** continues to work unchanged

## **FILES TO MODIFY**

### **Primary Changes**:
- `backend/app.py` - Add DuckDB logic to `/upload` endpoint
- `backend/duckdb_manager.py` - Ensure persistent connection support

### **No Changes Needed**:
- Frontend components
- Other API endpoints
- Excel processing logic
- Agent functionality
- File storage structure

This is a **discrete, additive change** to enable DuckDB persistence with document type recognition while maintaining 100% of existing functionality.

Once this is complete we need to test that all existing functionality works and that the duckdb table is correctly uploaded and persisted with proper document type identification.

Update the progress tracked in app.js - this is an update to Phase 2A- Integrate DuckDB with Document Type Recognition 