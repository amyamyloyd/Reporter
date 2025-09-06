# Backend Classification Simplification

## Overview

This document outlines the simplified classification approach that moves document classification from the conversational agent to the `/upload` endpoint, eliminating user interaction and streamlining the workflow.

## Current vs. Proposed Architecture

### Current Complex Flow
1. **Upload** → Field pattern matching → Mark as "New"
2. **User chats with agent** → Agent asks "What is this file?"
3. **Agent calls LLM** → Updates registry → Updates JSON

### Proposed Simplified Flow
1. **Upload** → Field pattern matching → **If no match → Call LLM directly** → Update registry + JSON
2. **No conversational classification needed**

## Key Changes

### 1. Move Classification to Upload Endpoint

**Location**: `backend/app.py` - `/upload` endpoint (lines 1332-1341)

**Current Logic**:
```python
else:
    print(f"📝 No existing document type found - marking as New")
    print(f"📝 New fields: {', '.join(all_fields)}")
    # Just marks as "New" - no classification
```

**New Logic**:
```python
else:
    print(f"📝 No existing document type found - calling LLM for classification")
    print(f"📝 New fields: {', '.join(all_fields)}")
    
    # Call LLM directly for classification
    classification_result = await classify_document_with_llm(all_fields, file.filename)
    
    if classification_result["success"]:
        document_type = classification_result["classification"]["document_type"]
        document_type_code = classification_result["classification"]["document_type_code"]
        description = classification_result["classification"]["description"]
        
        # Update doc_registry immediately
        registry_updated = add_new_document_type(
            db_conn,
            document_type,
            document_type_code, 
            all_fields,
            True,  # reuse_regularly
            description
        )
    else:
        # FALLBACK: Use filename to create document type
        base_name = os.path.splitext(file.filename)[0]
        document_type = base_name.replace('_', ' ').replace('-', ' ').title()
        document_type_code = base_name.replace('_', '').replace('-', '').upper()[:5]
        description = f"Document type derived from filename: {file.filename}"
        
        print(f"⚠️ Using filename fallback: {document_type} ({document_type_code})")
        
        # Still update registry with filename-based classification
        registry_updated = add_new_document_type(
            db_conn,
            document_type,
            document_type_code,
            all_fields,
            True,
            description
        )
```

### 2. Create LLM Classification Function

**New Function**: `classify_document_with_llm()` in `backend/app.py`

```python
async def classify_document_with_llm(fields: List[str], filename: str) -> Dict[str, Any]:
    """
    Classify document type using OpenAI LLM based on field names and filename
    
    This function analyzes the field names and filename to determine:
    - Professional document type name (WITHOUT dates/periods)
    - Unique document type code  
    - Description of purpose
    
    Args:
        fields: List of field names from Excel file
        filename: Original filename for context
        
    Returns:
        Dict with classification results or fallback to filename-based classification
    """
    try:
        from openai import OpenAI
        import os
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create context from fields and filename
        fields_context = ", ".join(fields)
        base_name = os.path.splitext(filename)[0]  # Remove extension
        
        system_prompt = """You are an expert document classifier for business data files.

Analyze the field names and filename to determine:
1. A professional, clear document type name (WITHOUT dates/periods)
2. A unique, short code (3-5 characters) for the document type  
3. A concise description of the document's purpose

CRITICAL RULES FOR DOCUMENT TYPE NAMES:
- Remove ALL temporal information (dates, quarters, months, years)
- Remove ALL version numbers and timestamps
- Focus on the CORE document type, not the time period
- Examples:
  * "sales-report-q1" → "Sales Report" (not "Sales Report Q1")
  * "vendors_2025-09-05_230247" → "Vendors" (not "Vendors 2025-09-05")
  * "inventory-march-2025" → "Inventory" (not "Inventory March 2025")
  * "financial-data-v2" → "Financial Data" (not "Financial Data V2")

REASONING:
- Document types should represent STRUCTURE, not TIME
- Q1, Q2, Q3 reports have the same fields and can reuse queries
- Weekly vendor updates have the same structure
- Focus on what the document IS, not when it was created

Guidelines:
- Document type names should be professional and descriptive
- Codes must be unique and memorable (e.g., "SALES", "VEND", "INV")
- Descriptions should be 1-2 sentences explaining the document's business purpose
- Base classification on field names, not filename

Return your response as valid JSON with these exact fields:
{
  "document_type": "Professional Document Type Name (NO DATES/PERIODS)",
  "document_type_code": "XXX", 
  "description": "Clear description of the document's purpose and use case"
}"""

        user_prompt = f"""Please classify this document based on the field names and filename:

Filename: {filename}
Fields: {fields_context}

IMPORTANT: Strip out ALL temporal information (dates, quarters, months, years, versions) from the document type name. Focus on the core document structure, not the time period.

Examples of what I want:
- "sales-report-q1" → "Sales Report" 
- "vendors_2025-09-05_230247" → "Vendors"
- "inventory-march-2025" → "Inventory"
- "financial-data-v2" → "Financial Data"

Analyze the fields and provide a professional document classification."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content.strip()
        classification = json.loads(ai_response)
        
        # Validate required fields
        required_fields = ["document_type", "document_type_code", "description"]
        for field in required_fields:
            if field not in classification:
                raise ValueError(f"Missing required field: {field}")
        
        return {
            "success": True,
            "classification": classification,
            "ai_response": ai_response
        }
        
    except Exception as e:
        print(f"❌ LLM classification failed: {e}")
        
        # FALLBACK: Use filename to create document type (also strip temporal info)
        base_name = os.path.splitext(filename)[0]
        
        # Remove common temporal patterns
        import re
        temporal_patterns = [
            r'_\d{4}-\d{2}-\d{2}_\d{6}',  # _2025-09-05_230247
            r'_\d{8}_\d{6}',               # _20250905_230247
            r'-\d{4}-\d{2}-\d{2}',        # -2025-09-05
            r'-\d{8}',                     # -20250905
            r'-q[1-4]',                    # -q1, -q2, -q3, -q4
            r'-january|-february|-march|-april|-may|-june',  # -march
            r'-july|-august|-september|-october|-november|-december',
            r'-jan|-feb|-mar|-apr|-may|-jun',  # -mar
            r'-jul|-aug|-sep|-oct|-nov|-dec',
            r'-v\d+',                      # -v1, -v2, -v3
            r'_\d{4}',                     # _2025
            r'-\d{4}',                     # -2025
        ]
        
        # Clean the base name
        clean_name = base_name
        for pattern in temporal_patterns:
            clean_name = re.sub(pattern, '', clean_name, flags=re.IGNORECASE)
        
        # Create document type from cleaned name
        document_type = clean_name.replace('_', ' ').replace('-', ' ').title()
        document_type_code = clean_name.replace('_', '').replace('-', '').upper()[:5]
        description = f"Document type derived from filename: {filename} (temporal info removed)"
        
        return {
            "success": False,
            "fallback": True,
            "classification": {
                "document_type": document_type,
                "document_type_code": document_type_code,
                "description": description
            },
            "error": str(e)
        }
```

### 3. Remove Classification from Chat Agent

**Remove from** `backend/app.py` - `/chat-agent` endpoint (lines 1734-1872):
- Remove `document_type_and_description` field handling
- Remove LLM classification logic
- Remove registry update logic
- Simplify conversation flow

**New simplified chat agent**:
```python
# Remove all classification logic - just handle other fields
elif field_name == "analysis_complete":
    json_data[field_name] = True
    json_data["ready_for_sql_agent"] = True
```

### 4. Update JSON Structure

**Remove from JSON**:
- `document_type_and_description` field
- `ai_description` field  
- `user_description` field
- `conversation_history` (classification parts)

**Keep in JSON**:
- `document_type` (set by upload)
- `document_type_code` (set by upload)
- `ready_for_duckdb` (set by upload)
- Other non-classification fields

## Temporal Information Removal

### Key Principle
Document types should represent **STRUCTURE**, not **TIME**. This enables:
- Query reusability across time periods
- Report reusability across time periods
- Consistent classification regardless of when created

### Examples

| Original Filename | Document Type | Document Type Code | Description |
|------------------|---------------|-------------------|-------------|
| `sales-report-q1.xlsx` | `Sales Report` | `SALES` | Quarterly sales data with revenue and customer metrics |
| `sales-report-q2.xlsx` | `Sales Report` | `SALES` | Quarterly sales data with revenue and customer metrics |
| `vendors_2025-09-05_230247.xlsx` | `Vendors` | `VEND` | Vendor information and contact details |
| `vendors_2025-09-12_230247.xlsx` | `Vendors` | `VEND` | Vendor information and contact details |
| `inventory-march-2025.xlsx` | `Inventory` | `INV` | Product inventory with quantities and costs |
| `inventory-april-2025.xlsx` | `Inventory` | `INV` | Product inventory with quantities and costs |
| `financial-data-v2.xlsx` | `Financial Data` | `FIN` | Financial metrics and accounting data |
| `employee-records-2025.xlsx` | `Employee Records` | `EMP` | Employee information and HR data |

### Temporal Patterns Removed
- `_2025-09-05_230247` (timestamp)
- `_20250905_230247` (compact timestamp)
- `-2025-09-05` (date)
- `-20250905` (compact date)
- `-q1`, `-q2`, `-q3`, `-q4` (quarters)
- `-january`, `-march`, `-december` (months)
- `-jan`, `-mar`, `-dec` (month abbreviations)
- `-v1`, `-v2`, `-v3` (versions)
- `_2025`, `-2025` (years)

## Benefits

### 1. **Simpler Architecture**
- Classification happens once at upload
- No complex conversational flow needed
- Cleaner, more maintainable code

### 2. **Better User Experience**
- No manual file description required
- Fully automated classification
- Faster workflow

### 3. **Query and Report Reusability**
- Q1 and Q2 sales reports can use the same queries
- Weekly vendor updates can use the same report templates
- Consistent document type regardless of time period

### 4. **Meaningful Fallbacks**
- Filename-based classification instead of generic "New"
- Temporal information properly stripped
- Still functional for future pattern matching

## Files to Modify

### 1. **`backend/app.py`**
- Modify `/upload` endpoint (lines 1332-1341)
- Add `classify_document_with_llm()` function
- Remove classification from `/chat-agent` endpoint

### 2. **`backend/agents/upload_agent.py`**
- Remove `_classify_document_type()` method
- Remove classification-related logic

### 3. **Frontend** (if needed)
- Remove classification UI elements
- Simplify conversation flow

## Implementation Priority

1. **Phase 1**: Implement `classify_document_with_llm()` function
2. **Phase 2**: Update `/upload` endpoint with new classification logic
3. **Phase 3**: Remove classification from chat agent
4. **Phase 4**: Test with various filename patterns
5. **Phase 5**: Update frontend (if needed)

## Testing Scenarios

### Test Cases
1. **LLM Success**: File with clear field patterns
2. **LLM Failure**: File with unclear patterns → filename fallback
3. **Temporal Removal**: Files with dates/quarters/versions
4. **Registry Updates**: New document types added correctly
5. **Pattern Matching**: Future uploads match existing types

### Sample Test Files
- `sales-report-q1.xlsx` → Should become "Sales Report"
- `vendors_2025-09-05_230247.xlsx` → Should become "Vendors"
- `inventory-march-2025.xlsx` → Should become "Inventory"
- `financial-data-v2.xlsx` → Should become "Financial Data"

## Conclusion

This simplified approach eliminates the need for user interaction during classification while maintaining intelligent document type detection. The focus on removing temporal information ensures that documents of the same structural type are classified consistently, enabling query and report reusability across different time periods.
