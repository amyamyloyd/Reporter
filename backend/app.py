from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import duckdb
from pathlib import Path

# Import Phase 1 modules
from excel_processor import extract_file_metadata_from_saved_file, validate_excel_files
from duckdb_manager import create_persistent_database

# Import Phase 2A modules
from agents.file_analyzer import analyze_single_file

# Load environment variables
load_dotenv()

def generate_standard_table_name(filename: str, document_type_code: str, timestamp: str) -> str:
    """
    Generate standardized DuckDB table name in format: filename_document_type_code_YYYYMMDD_HHMMSS
    
    Args:
        filename: Original Excel filename (without extension)
        document_type_code: Short lowercase document type code (e.g., 'gl', 'campaign')
        timestamp: Upload timestamp in format 'YYYY-MM-DD_HHMMSS'
    
    Returns:
        Standardized table name safe for DuckDB
    """
    # Clean filename (remove spaces, special chars, keep alphanumeric and underscores)
    clean_filename = re.sub(r'[^a-zA-Z0-9_]', '_', filename)
    
    # Clean document type code (ensure lowercase, alphanumeric only)
    clean_doc_code = re.sub(r'[^a-zA-Z0-9]', '', document_type_code.lower())
    
    # Clean timestamp (remove non-alphanumeric chars)
    clean_timestamp = re.sub(r'[^0-9]', '', timestamp)
    
    # Ensure table name starts with letter (DuckDB requirement)
    if clean_filename and clean_filename[0].isdigit():
        clean_filename = 'tbl_' + clean_filename
    
    # Generate final table name
    table_name = f"{clean_filename}_{clean_doc_code}_{clean_timestamp}"
    
    # Final validation - ensure table name is valid for DuckDB
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        # If still invalid, use completely safe fallback
        table_name = f"excel_data_{clean_timestamp}"
    
    return table_name

# Create FastAPI app
app = FastAPI(title="AI Excel Reporting API", version="1.0.0")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for analysis results (session-based)
analysis_storage = {}



@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Excel Reporting API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "environment": os.getenv("ENVIRONMENT", "development")}

@app.get("/check-tables")
async def check_tables():
    """Check what tables exist in DuckDB and their structure"""
    try:
        conn = create_persistent_database()
        
        # Get all tables using DuckDB's information_schema
        tables_result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
        tables_info = []
        
        for table_row in tables_result:
            table_name = table_row[0]
            
            # Get table schema (columns)
            schema_result = conn.execute(f"DESCRIBE {table_name}").fetchall()
            columns = []
            for col in schema_result:
                columns.append({
                    "name": col[0],
                    "type": col[1],
                    "null": col[2],
                    "key": col[3],
                    "default": col[4]
                })
            
            # Get record count
            count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            record_count = count_result[0] if count_result else 0
            
            # Get sample data (first 3 rows)
            try:
                sample_result = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
                sample_data = [list(row) for row in sample_result]
            except Exception as e:
                sample_data = f"Error reading sample: {str(e)}"
            
            tables_info.append({
                "table_name": table_name,
                "columns": columns,
                "record_count": record_count,
                "sample_data": sample_data
            })
        
        conn.close()
        
        return {
            "success": True,
            "database": "excel_reporting.db",
            "total_tables": len(tables_info),
            "tables": tables_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check tables: {str(e)}",
            "database": "excel_reporting.db"
        }

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """File upload endpoint with validation and metadata extraction"""
    try:
        # Validate files using Phase 1 module
        validation = validate_excel_files(files)
        
        if validation["errors"]:
            raise HTTPException(status_code=400, detail="Validation errors: " + "; ".join(validation["errors"]))
        
        if not validation["valid_files"]:
            raise HTTPException(status_code=400, detail="No valid files provided")
        
        # Create persistent database for session (Phase 1 foundation)
        db_conn = create_persistent_database()
        
        # Create JSON file for each uploaded file
        import json
        import os
        from datetime import datetime
        
        # Ensure the files directory exists
        os.makedirs("stored_queries/files", exist_ok=True)
        
        # Track JSON filenames for response
        json_filenames = []
        
        for file in validation["valid_files"]:
            
            # Create unique filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            base_name = os.path.splitext(file.filename)[0]  # Remove .xlsx extension
            json_filename = f"{base_name}_{timestamp}.json"
            excel_filename = file.filename
            
            json_path = f"stored_queries/{json_filename}"
            excel_path = f"stored_queries/files/{excel_filename}"
            
            # STEP 1: Save the Excel file FIRST (no processing)
            with open(excel_path, 'wb') as f:
                content = await file.read()
                f.write(content)
                print(f"✅ Excel file saved: {excel_path} ({len(content)} bytes)")
            
            # STEP 2: Extract metadata from the SAVED file (not the uploaded file)
            file_metadata = extract_file_metadata_from_saved_file(excel_path)
            
            # Extract fields from sheets
            all_fields = []
            normalized_fields = []
            if "sheets" in file_metadata:
                for sheet_name, sheet_data in file_metadata["sheets"].items():
                    if "fields" in sheet_data:
                        all_fields.extend(sheet_data["fields"])
                    if "normalized_fields" in sheet_data:
                        normalized_fields.extend(sheet_data["normalized_fields"])
                # Remove duplicates while preserving order
                all_fields = list(dict.fromkeys(all_fields))
                normalized_fields = list(dict.fromkeys(normalized_fields))
            
            # STEP 3: Check if document type already exists by comparing fields
            document_type = "New"
            document_type_code = "new"
            is_new_document = True
            version = "1.0"
            
            try:
                # Check if doc_registry table exists and query for matching document types
                # Use a simple try/catch approach instead of information_schema
                fields_string = '|'.join(sorted(all_fields))  # Create comparable fields string
                
                # Query for exact field matches
                match_result = db_conn.execute("""
                    SELECT document_type, document_type_code 
                    FROM doc_registry 
                    WHERE field_pattern = ? 
                    LIMIT 1
                """, [fields_string])
                
                match = match_result.fetchone()
                if match:
                    document_type = match[0]
                    document_type_code = match[1]
                    is_new_document = False
                    print(f"✅ Document type match found: {document_type} ({document_type_code})")
                    print(f"✅ Fields matched: {', '.join(all_fields)}")
                else:
                    print(f"📝 No existing document type found - marking as New")
                    print(f"📝 New fields: {', '.join(all_fields)}")
                    
            except Exception as e:
                print(f"⚠️ Error checking document registry: {e}")
                print(f"📝 Falling back to New document type")
                document_type = "New"
                document_type_code = "new"
                is_new_document = True
            
            # STEP 3.5: Manage document versioning
            try:
                from duckdb_manager import manage_document_version
                
                # Call version management function
                version_info = manage_document_version(
                    db_conn, 
                    document_type_code, 
                    fields_string, 
                    is_new_document
                )
                
                if version_info.get("registry_updated"):
                    version = version_info.get("version", "1.0")
                    print(f"✅ Version management successful: {document_type_code} → {version}")
                else:
                    print(f"⚠️ Version management failed: {version_info.get('error', 'Unknown error')}")
                    version = "1.0"  # Fallback
                    
            except Exception as e:
                print(f"❌ Version management error: {e}")
                version = "1.0"  # Fallback
            
            # Create JSON structure
            json_data = {
                "filename": excel_filename,  # Reference the saved Excel file
                "sheets": file_metadata.get("sheets", {}),
                "fields": all_fields,  # Original field names for display
                "normalized_fields": normalized_fields,  # Clean field names for DuckDB
                "record_count": sum(sheet.get("row_count", 0) for sheet in file_metadata.get("sheets", {}).values()),
                "upload_timestamp": timestamp,
                "file_size": len(content),
                "content_type": file.content_type,
                "document_type": document_type,  # Use determined document type
                "document_type_code": document_type_code,  # Use determined document type code
                "version": version,  # Add version field from version management
                "conversation_status": "completed" if document_type != "New" else "pending",
                "ready_for_sql_agent": True if document_type != "New" else False
            }
            
            # Save JSON file
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            print(f"Created JSON file: {json_path}")
            
            # Track the JSON filename for response
            json_filenames.append({
                "excel_filename": excel_filename,
                "json_filename": json_filename
            })
            
            # VERIFY: Check if saved Excel file is valid before proceeding
            import os
            if os.path.exists(excel_path):
                file_size = os.path.getsize(excel_path)
                print(f"✅ Saved file verified: {excel_path} ({file_size} bytes)")
                if file_size == 0:
                    print(f"❌ ERROR: Saved file is empty!")
                    continue
                if file_size != len(content):
                    print(f"❌ ERROR: File size mismatch! Expected: {len(content)}, Got: {file_size}")
                    continue
            else:
                print(f"❌ ERROR: Saved file not found!")
                continue
            
            # CRITICAL: DuckDB Integration - Create table for EVERY file
            print(f"🔄 Creating DuckDB table for: {excel_filename}")
            
            try:
                # Generate table name from original filename
                # Format: {original_filename}_{timestamp}
                timestamp_short = timestamp.replace('-', '').replace(':', '').replace(' ', '')
                # Clean filename for DuckDB (remove spaces, special chars)
                clean_filename = re.sub(r'[^a-zA-Z0-9_]', '_', base_name)
                duckdb_table_name = f"{clean_filename}_{timestamp_short}"
                
                print(f"Generated table name: {duckdb_table_name}")
                
                # SIMPLIFIED: Create DuckDB table directly from Excel file
                print(f"🔄 Creating DuckDB table: {duckdb_table_name}")
                
                try:
                    # Use the simple working pattern: load Excel, register DataFrame, create table
                    import pandas as pd
                    df = pd.read_excel(excel_path, engine='openpyxl')
                    print(f"✅ Loaded Excel data: {df.shape[0]} rows, {df.shape[1]} columns")
                    
                    # Register DataFrame and create table (the working pattern)
                    db_conn.register('temp_df', df)
                    db_conn.execute(f"CREATE TABLE {duckdb_table_name} AS SELECT * FROM temp_df")
                    db_conn.unregister('temp_df')
                    print(f"✅ Table created successfully")
                    
                    # Verify table creation
                    result = db_conn.execute(f"SELECT COUNT(*) FROM {duckdb_table_name}")
                    row_count = result.fetchone()[0]
                    print(f"✅ Table verified: {row_count} rows")
                    
                    print(f"✅ SUCCESS: DuckDB table created: {duckdb_table_name}")
                    
                    # Update JSON with DuckDB metadata
                    json_data.update({
                        "duckdb_table_name": duckdb_table_name,
                        "duckdb_loaded": True,
                        "is_current_version": True
                    })
                    
                    # Save updated JSON with DuckDB metadata
                    with open(json_path, 'w') as f:
                        json.dump(json_data, f, indent=2)
                    
                    print(f"✅ JSON updated with DuckDB metadata")
                    
                except Exception as e:
                    print(f"❌ CRITICAL ERROR: Failed to create DuckDB table: {duckdb_table_name}")
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Still update JSON but mark as not loaded
                    json_data.update({
                        "duckdb_table_name": None,
                        "duckdb_loaded": False,
                        "is_current_version": True
                    })
                    
            except Exception as e:
                print(f"❌ CRITICAL ERROR: DuckDB integration failed: {e}")
                print(f"❌ Error type: {type(e).__name__}")
                print(f"❌ Error details: {str(e)}")
                # Update JSON with error state
                json_data.update({
                    "duckdb_table_name": None,
                    "duckdb_loaded": False,
                    "is_current_version": True,
                    "duckdb_error": str(e)
                })
                
                # Save updated JSON even with errors
                with open(json_path, 'w') as f:
                    json.dump(json_data, f, indent=2)
        
        # Close database connection
        if db_conn:
            db_conn.close()
            print("✅ Database connection closed")
        
        # Return files array that frontend expects for AgentChat
        files_data = []
        for i, file in enumerate(validation["valid_files"]):
            # Get metadata from the saved file
            excel_path = f"stored_queries/files/{file.filename}"
            file_metadata = extract_file_metadata_from_saved_file(excel_path) if os.path.exists(excel_path) else {}
            
            # Combine fields from all sheets for the frontend
            all_fields = []
            if "sheets" in file_metadata:
                for sheet_name, sheet_data in file_metadata["sheets"].items():
                    if "fields" in sheet_data:
                        all_fields.extend(sheet_data["fields"])
                # Remove duplicates while preserving order
                all_fields = list(dict.fromkeys(all_fields))
            
            # Get the JSON filename from our tracked list (more efficient than glob search)
            json_filename = None
            for json_info in json_filenames:
                if json_info["excel_filename"] == file.filename:
                    json_filename = json_info["json_filename"]
                    break
            
            # Fallback: if not found in tracking (shouldn't happen), use glob search
            if not json_filename:
                import glob
                base_name = os.path.splitext(file.filename)[0]
                json_files = glob.glob(f"stored_queries/{base_name}_*.json")
                
                if json_files:
                    # Use the most recent JSON file
                    json_filename = os.path.basename(sorted(json_files)[-1])
                else:
                    # Final fallback: create new filename (shouldn't happen)
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                    json_filename = f"{base_name}_{timestamp}.json"
            
            files_data.append({
                "name": file.filename,  # Frontend expects 'name' property
                "size": file.size,
                "content_type": file.content_type,
                "fields": all_fields,  # Combined fields from all sheets
                "sheets": file_metadata.get("sheets", {}) if file_metadata else {},
                "file_index": i,
                "json_filename": json_filename  # Include JSON filename for ChatAgent
            })
        
        return {
            "success": True,
            "message": f"Successfully processed {len(validation['valid_files'])} files",
            "files": files_data,  # This is what AgentChat expects
            "validation": validation,
            "metadata": {}, # Metadata is now extracted from saved files
            "database_ready": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in file upload: {e}")
        raise HTTPException(status_code=500, detail="File processing failed")

# Phase 2A: File Analysis Endpoints

@app.post("/chat-agent")
async def chat_agent_conversation(request: Dict[str, Any]):
    """
    Progressive ChatAgent conversation to collect user input and update JSON files
    
    Args:
        request: Dict containing json_filename, user_response, and conversation_step
        
    Returns:
        Dict with next question, conversation status, and updated JSON
    """
    try:
        # Extract request data
        json_filename = request.get("json_filename", "")
        user_response = request.get("user_response", "")
        conversation_step = request.get("conversation_step", 0)
        
        # Validate required fields
        if not json_filename:
            raise HTTPException(status_code=400, detail="Missing json_filename")
        
        # Construct full path to JSON file
        json_path = f"stored_queries/{json_filename}"
        
        # Check if JSON file exists
        if not os.path.exists(json_path):
            raise HTTPException(status_code=404, detail=f"JSON file not found: {json_filename}")
        
        # Read current JSON data
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        # Check document type and handle conversation flow accordingly
        document_type = json_data.get('document_type', '')
        
        # Check if document is already ready for SQL agent (from upload endpoint)
        if json_data.get("ready_for_sql_agent", False):
            document_type = json_data.get("document_type", "")
            print(f"Document already ready for SQL agent: {document_type}")
            
            return {
                "success": True,
                "conversation_status": "completed",
                "current_question": f"You uploaded a {document_type} document - ready to query!",
                "next_step": "complete",
                "total_steps": 0,
                "current_step": 0,
                "json_data": json_data,
                "message": f"Document identified as {document_type} - ready for SQL agent"
            }
        
        # Initialize conversation flow for new/unknown document types
        conversation_flow = [
            {
                "step": 1,
                "question": f"Per my analysis, this file includes {', '.join(json_data.get('fields', []))} with {json_data.get('record_count', 0)} records. Is that correct?",
                "field": "user_confirmation",
                "next_step": 2
            },
            {
                "step": 2,
                "question": "What type of document is this? (e.g., General Ledger, Vendor Reference, Campaign Data) and please provide a brief description of its purpose",
                "field": "document_type_and_description",
                "next_step": 3
            },
            {
                "step": 3,
                "question": "Ready to complete analysis",
                "field": "analysis_complete",
                "next_step": "complete"
            }
        ]
        
        # Handle user response if provided
        if user_response and conversation_step > 0:
            current_step = conversation_flow[conversation_step - 1]
            field_name = current_step["field"]
            
            # Process response based on field type
            if field_name == "user_confirmation":
                # Check if response is affirmative
                affirmative_responses = ["yes", "sure", "correct", "that's right", "yep", "ok", "good", "right"]
                is_affirmative = any(response in user_response.lower() for response in affirmative_responses)
                
                if not is_affirmative:
                    return {
                        "success": False,
                        "error": "Please confirm that the field analysis is correct before proceeding"
                    }
                
                json_data[field_name] = True
            elif field_name == "document_type_and_description":
                # Use LLM classification instead of regex patterns
                response_text = user_response.strip()
                
                try:
                    # Call the new LLM classification endpoint
                    from openai import OpenAI
                    
                    # Initialize OpenAI client
                    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    
                    # Create system prompt for document classification
                    system_prompt = """You are an expert document classifier for business data files.

Your task is to analyze a user's description of a document and determine:
1. A professional, clear document type name
2. A unique, short code (3-5 characters) for the document type
3. A concise description of the document's purpose

Guidelines:
- Document type names should be professional and descriptive (e.g., "Weekly Sales Report", "General Ledger", "Vendor Reference")
- Codes must be unique and memorable (e.g., "WSR", "GL", "VR")
- Descriptions should be 1-2 sentences explaining the document's business purpose
- Be specific but not overly verbose

Return your response as valid JSON with these exact fields:
{
  "document_type": "Professional Document Type Name",
  "document_type_code": "XXX",
  "description": "Clear description of the document's purpose and use case"
}"""

                    # Create user prompt
                    user_prompt = f"""Please classify this document based on the user's description:

User Description: "{response_text}"

Analyze the description and provide a professional document classification."""

                    # Call OpenAI API
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=200,
                        temperature=0.1
                    )
                    
                    # Extract response content
                    ai_response = response.choices[0].message.content.strip()
                    
                    # Parse JSON response
                    try:
                        classification = json.loads(ai_response)
                        
                        # Validate required fields
                        required_fields = ["document_type", "document_type_code", "description"]
                        for field in required_fields:
                            if field not in classification:
                                raise ValueError(f"Missing required field: {field}")
                        
                        # Store AI classification results
                        document_type = classification["document_type"]
                        document_type_code = classification["document_type_code"]
                        ai_description = classification["description"]
                        
                        json_data["document_type"] = document_type
                        json_data["document_type_code"] = document_type_code
                        json_data["ai_description"] = ai_description
                        json_data["user_description"] = response_text
                        json_data["ready_for_duckdb"] = True
                        
                        print(f"✅ AI Classification successful: {document_type} ({document_type_code})")
                        
                        # Update document registry with the new document type
                        try:
                            from duckdb_manager import add_new_document_type
                            conn = create_persistent_database()
                            
                            # Get the original fields from the JSON (for registry matching)
                            all_fields = json_data.get('fields', [])
                            
                            registry_updated = add_new_document_type(
                                conn,
                                document_type,
                                document_type_code,
                                all_fields,  # Use original field names for registry matching
                                True,  # reuse_regularly = True (assume all are reusable)
                                ai_description  # Use AI-generated description
                            )
                            
                            if registry_updated:
                                print(f"✅ Document type '{document_type}' added to registry")
                            else:
                                print(f"⚠️  Failed to add document type to registry")
                                
                            conn.close()
                            
                        except Exception as e:
                            print(f"⚠️  Registry update failed: {e}")
                            # Continue even if registry update fails
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse AI response as JSON: {e}")
                        print(f"AI Response: {ai_response}")
                        
                        # Fallback: create basic classification
                        words = response_text.split()
                        if len(words) >= 2:
                            fallback_type = ' '.join(words[:2]).strip()
                        else:
                            fallback_type = response_text[:50].strip()
                        
                        fallback_code = fallback_type.replace(' ', '').upper()[:5]
                        
                        json_data["document_type"] = fallback_type
                        json_data["document_type_code"] = fallback_code
                        json_data["ai_description"] = f"Document classified as {fallback_type} based on user description"
                        json_data["user_description"] = response_text
                        json_data["ready_for_duckdb"] = True
                        
                        print(f"⚠️  Using fallback classification: {fallback_type} ({fallback_code})")
                        
                except Exception as e:
                    print(f"❌ LLM classification failed: {e}")
                    
                    # Ultimate fallback
                    fallback_type = "Unknown Document Type"
                    fallback_code = "UNK"
                    
                    json_data["document_type"] = fallback_type
                    json_data["document_type_code"] = fallback_code
                    json_data["ai_description"] = "Document classification failed - using fallback"
                    json_data["user_description"] = response_text
                    json_data["ready_for_duckdb"] = True
                    
                    print(f"⚠️  Using ultimate fallback: {fallback_type} ({fallback_code})")
                
            elif field_name == "analysis_complete":
                json_data[field_name] = True
                json_data["ready_for_sql_agent"] = True
            
            # Update conversation history with enhanced information
            if "conversation_history" not in json_data:
                json_data["conversation_history"] = []
            
            # Create conversation history entry
            history_entry = {
                "step": conversation_step,
                "question": current_step["question"],
                "user_response": user_response,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add LLM response if this was a document classification step
            if field_name == "document_type_and_description":
                if "ai_description" in json_data:
                    history_entry["llm_response"] = {
                        "document_type": json_data.get("document_type"),
                        "document_type_code": json_data.get("document_type_code"),
                        "ai_description": json_data.get("ai_description")
                    }
            
            json_data["conversation_history"].append(history_entry)
            
            # Save updated JSON
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            print(f"Updated JSON file: {json_path} with {field_name}")
        
        # Determine next step
        if conversation_step == 0:
            # First time - start conversation
            next_step = 1
            current_question = conversation_flow[0]["question"]
            conversation_status = "started"
        elif conversation_step < len(conversation_flow):
            # Continue conversation - determine the next step to show
            if conversation_step == 1:
                # After step 1, show step 2 question
                next_step = 2
                current_question = conversation_flow[1]["question"]
                conversation_status = "in_progress"
            elif conversation_step == 2:
                # After step 2, check if document classification is complete
                if json_data.get('document_type') and json_data.get('document_type_code'):
                    # Document classification is complete, show step 3
                    next_step = 3
                    current_question = f"Great! So this is a {json_data.get('document_type')} ({json_data.get('document_type_code')}) - ready to query, create a report, or do you have another file to upload? This document is being saved as {json_data.get('document_type')} @{json_data.get('filename', '').replace('.xlsx', '')}_{json_data.get('upload_timestamp', '')}.json"
                    conversation_status = "in_progress"
                else:
                    # Still waiting for document classification response
                    next_step = 2
                    current_question = "Please provide a description of what type of document this is."
                    conversation_status = "waiting_for_input"
            elif conversation_step == 3:
                # After step 3, show completion message
                next_step = "complete"
                current_question = f"Perfect! I've classified this as a {json_data.get('document_type', 'document')} ({json_data.get('document_type_code', 'DOC')}). This document is being saved as {json_data.get('document_type', 'document')} @{json_data.get('filename', '').replace('.xlsx', '')}_{json_data.get('upload_timestamp', '')}.json. The document is now ready for DuckDB processing and SQL queries."
                conversation_status = "completed"
                json_data["analysis_complete"] = True
                json_data["ready_for_duckdb"] = True
                
                # Now create the DuckDB table with the Excel data
                try:
                    from duckdb_manager import dataframe_to_table
                    import pandas as pd
                    
                    # Read the Excel file to get the data
                    excel_filename = json_data.get('filename', '')
                    if excel_filename:
                        excel_path = f"stored_queries/files/{excel_filename}"
                        if os.path.exists(excel_path):
                            # Read Excel file
                            df = pd.read_excel(excel_path)
                            
                            # Generate simple, clean table name
                            timestamp_short = json_data.get('upload_timestamp', '').replace('-', '').replace(':', '').replace(' ', '')
                            
                            duckdb_table_name = f"excel_data_{timestamp_short}"
                            
                            print(f"Generated table name: {duckdb_table_name}")
                            
                            # Create DuckDB connection and table
                            conn = create_persistent_database()
                            table_created = dataframe_to_table(conn, df, duckdb_table_name)
                            conn.close()
                            
                            if table_created:
                                print(f"✅ DuckDB table created: {duckdb_table_name}")
                                json_data["duckdb_table_name"] = duckdb_table_name
                                json_data["duckdb_loaded"] = True
                            else:
                                print(f"❌ Failed to create DuckDB table: {duckdb_table_name}")
                                json_data["duckdb_table_name"] = None
                                json_data["duckdb_loaded"] = False
                                json_data["duckdb_error"] = "Table creation failed"
                        else:
                            print(f"❌ Excel file not found: {excel_path}")
                            json_data["duckdb_error"] = f"Excel file not found: {excel_path}"
                    else:
                        print(f"❌ No filename in JSON data")
                        json_data["duckdb_error"] = "No filename in JSON data"
                        
                except Exception as e:
                    print(f"❌ DuckDB table creation failed: {e}")
                    json_data["duckdb_error"] = str(e)
                    json_data["duckdb_loaded"] = False
        else:
            # Conversation already complete
            current_question = "Conversation already completed."
            conversation_status = "completed"
            next_step = "complete"
        
        # Save final state if completed
        if conversation_status == "completed":
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2)
        
        return {
            "success": True,
            "conversation_status": conversation_status,
            "current_question": current_question,
            "next_step": next_step,
            "total_steps": len(conversation_flow),
            "current_step": conversation_step,
            "json_data": json_data,
            "message": f"Conversation {conversation_status}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat agent conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Chat agent conversation failed: {str(e)}")

@app.post("/classify-document")
async def classify_document(request: Dict[str, Any]):
    """
    Classify document type using OpenAI LLM based on user description
    
    This endpoint takes a user's description of a document and uses OpenAI
    to automatically determine the document type, generate a unique code,
    and create a professional description.
    
    Args:
        request: Dict containing user_description
        
    Returns:
        Dict with AI-determined document classification
    """
    try:
        # Extract user description
        user_description = request.get("user_description", "").strip()
        
        if not user_description:
            raise HTTPException(status_code=400, detail="Missing user_description")
        
        # Import OpenAI client
        from openai import OpenAI
        import os
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create system prompt for document classification
        system_prompt = """You are an expert document classifier for business data files.

Your task is to analyze a user's description of a document and determine:
1. A professional, clear document type name
2. A unique, short code (3-5 characters) for the document type
3. A concise description of the document's purpose

Guidelines:
- Document type names should be professional and descriptive (e.g., "Weekly Sales Report", "General Ledger", "Vendor Reference")
- Codes must be unique and memorable (e.g., "WSR", "GL", "VR")
- Descriptions should be 1-2 sentences explaining the document's business purpose
- Be specific but not overly verbose

Return your response as valid JSON with these exact fields:
{
  "document_type": "Professional Document Type Name",
  "document_type_code": "XXX",
  "description": "Clear description of the document's purpose and use case"
}"""

        # Create user prompt
        user_prompt = f"""Please classify this document based on the user's description:

User Description: "{user_description}"

Analyze the description and provide a professional document classification."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        # Extract response content
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            classification = json.loads(ai_response)
            
            # Validate required fields
            required_fields = ["document_type", "document_type_code", "description"]
            for field in required_fields:
                if field not in classification:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure document type code is unique
            # TODO: Implement uniqueness check against existing codes
            
            print(f"✅ AI Classification successful: {classification['document_type']} ({classification['document_type_code']})")
            
            return {
                "success": True,
                "classification": classification,
                "ai_response": ai_response
            }
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse AI response as JSON: {e}")
            print(f"AI Response: {ai_response}")
            
            # Fallback: create basic classification
            words = user_description.split()
            if len(words) >= 3:
                fallback_type = " ".join(words[:3]).title()
            else:
                fallback_type = user_description.title()
            fallback_code = fallback_type.replace(" ", "")[:5].upper()
            
            return {
                "success": True,
                "classification": {
                    "document_type": fallback_type,
                    "document_type_code": fallback_code,
                    "description": f"Document classified as {fallback_type} based on user description"
                },
                "ai_response": ai_response,
                "fallback_used": True
            }
            
    except Exception as e:
        print(f"❌ Document classification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document classification failed: {str(e)}")

@app.post("/save-analysis")
async def save_analysis(analysis: Dict[str, Any]):
    """
    Save analysis results to temporary storage
    
    Args:
        analysis: Dict containing analysis results to save
        
    Returns:
        Dict with save confirmation
    """
    try:
        # Generate a simple session ID (in production, use proper session management)
        session_id = "default_session"
        
        # Store analysis results
        if session_id not in analysis_storage:
            analysis_storage[session_id] = []
        
        analysis_storage[session_id].append(analysis)
        
        return {
            "success": True,
            "message": "Analysis results saved successfully",
            "session_id": session_id,
            "total_saved": len(analysis_storage[session_id])
        }
        
    except Exception as e:
        print(f"Error saving analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save analysis: {str(e)}")

@app.get("/list-json-files")
async def list_json_files():
    """
    List all available JSON files in stored_queries directory
    
    Returns:
        Dict with list of JSON files
    """
    try:
        import glob
        import os
        
        # List all JSON files in stored_queries directory
        json_files = []
        json_pattern = "stored_queries/*.json"
        
        for file_path in glob.glob(json_pattern):
            filename = os.path.basename(file_path)
            json_files.append(filename)
        
        # Sort files by creation time (newest first)
        json_files.sort(key=lambda x: os.path.getctime(f"stored_queries/{x}"), reverse=True)
        
        return {
            "success": True,
            "files": json_files,
            "count": len(json_files),
            "message": f"Found {len(json_files)} JSON files"
        }
        
    except Exception as e:
        print(f"Error listing JSON files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list JSON files: {str(e)}")

@app.get("/get-analysis/{session_id}")
async def get_analysis(session_id: str):
    """
    Retrieve saved analysis results for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Dict with saved analysis results
    """
    try:
        if session_id not in analysis_storage:
            return {
                "success": False,
                "message": "No analysis results found for this session",
                "results": []
            }
        
        return {
            "success": True,
            "message": f"Retrieved {len(analysis_storage[session_id])} analysis results",
            "results": analysis_storage[session_id],
            "session_id": session_id
        }
        
    except Exception as e:
        print(f"Error retrieving analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis: {str(e)}")

@app.get("/doc-registry")
async def get_doc_registry():
    """
    Display the contents of the doc_registry table
    
    Returns:
        Dict with document registry contents and metadata
    """
    try:
        # Create database connection
        conn = create_persistent_database()
        
        # Check if doc_registry table exists
        table_exists = conn.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'doc_registry'
        """).fetchone()[0]
        
        if table_exists == 0:
            return {
                "success": True,
                "message": "doc_registry table does not exist yet",
                "registry": [],
                "count": 0,
                "table_exists": False
            }
        
        # Get all records from doc_registry
        registry_result = conn.execute("""
            SELECT 
                id,
                document_type,
                document_type_code,
                field_pattern,
                reuse_regularly,
                created_date,
                updated_date,
                description,
                example_filename,
                latest_version
            FROM doc_registry 
            ORDER BY created_date DESC
        """).fetchall()
        
        # Convert to list of dictionaries for JSON serialization
        registry_data = []
        for row in registry_result:
            registry_data.append({
                "id": row[0],
                "document_type": row[1],
                "document_type_code": row[2],
                "field_pattern": row[3],
                "reuse_regularly": bool(row[4]),
                "created_date": row[5],
                "updated_date": row[6],
                "description": row[7],
                "example_filename": row[8],
                "latest_version": row[9]
            })
        
        # Get table schema information
        schema_result = conn.execute("DESCRIBE doc_registry").fetchall()
        schema_info = []
        for col in schema_result:
            schema_info.append({
                "column_name": col[0],
                "data_type": col[1],
                "nullable": col[2] if len(col) > 2 else None,
                "default": col[3] if len(col) > 3 else None
            })
        
        # Close database connection
        conn.close()
        
        return {
            "success": True,
            "message": f"Retrieved {len(registry_data)} document types from registry",
            "registry": registry_data,
            "count": len(registry_data),
            "table_exists": True,
            "schema": schema_info,
            "table_info": {
                "name": "doc_registry",
                "total_records": len(registry_data)
            }
        }
        
    except Exception as e:
        print(f"Error retrieving doc_registry: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to retrieve doc_registry: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
