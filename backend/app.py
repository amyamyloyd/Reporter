from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import os
import json
import re
from datetime import datetime
from dotenv import load_dotenv

# Import Phase 1 modules
from excel_processor import extract_file_metadata_from_saved_file, validate_excel_files
from duckdb_manager import create_memory_database

# Import Phase 2A modules
from agents.file_analyzer import analyze_single_file

# Load environment variables
load_dotenv()

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
        conn = create_memory_database()
        
        # Get all tables
        tables_result = conn.execute("SHOW TABLES").fetchall()
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
        
        # Create in-memory database for session (Phase 1 foundation)
        db_conn = create_memory_database()
        
        # Create JSON file for each uploaded file
        import json
        import os
        from datetime import datetime
        
        # Ensure the files directory exists
        os.makedirs("stored_queries/files", exist_ok=True)
        
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
                "conversation_status": "completed" if document_type != "New" else "pending",
                "ready_for_sql_agent": True if document_type != "New" else False
            }
            
            # Save JSON file
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            print(f"Created JSON file: {json_path}")
            
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
            
            # Find the actual JSON file that was created for this Excel file
            import glob
            base_name = os.path.splitext(file.filename)[0]
            json_files = glob.glob(f"stored_queries/{base_name}_*.json")
            
            if json_files:
                # Use the most recent JSON file
                json_filename = os.path.basename(sorted(json_files)[-1])
            else:
                # Fallback: create new filename (shouldn't happen)
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
                "question": f"Perfect! I've classified this as a {json_data.get('document_type', 'document')} ({json_data.get('document_type_code', 'DOC')}). The document is now ready for DuckDB processing and SQL queries.",
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
                # Parse user response to extract document type and description
                response_text = user_response.strip()
                
                # Try to extract document type (first part before any punctuation or "and")
                # Look for common document type patterns
                doc_type_patterns = [
                    r'^([A-Za-z\s]+?)(?:\s+and|\s*[,;]\s*|\s*[-–]\s*|\s*\(|$)',
                    r'^([A-Za-z\s]+?)(?:\s+description|\s+purpose|\s+is\s+a|\s+for)',
                    r'^([A-Za-z\s]+?)(?:\s+data|\s+records|\s+file)'
                ]
                
                document_type = None
                for pattern in doc_type_patterns:
                    match = re.search(pattern, response_text)
                    if match:
                        document_type = match.group(1).strip()
                        break
                
                # If no pattern match, take first 2-3 words as document type
                if not document_type:
                    words = response_text.split()
                    if len(words) >= 2:
                        document_type = ' '.join(words[:2]).strip()
                    else:
                        document_type = response_text[:50].strip()  # Fallback
                
                # Generate document type code (short version)
                document_type_code = document_type.replace(' ', '').upper()[:8]
                
                # Store both document type and description
                json_data["document_type"] = document_type
                json_data["document_type_code"] = document_type_code
                json_data["user_description"] = response_text
                json_data["ready_for_duckdb"] = True
                
                print(f"Extracted document type: '{document_type}' with code: '{document_type_code}'")
                
                # Update document registry with the new document type
                try:
                    from duckdb_manager import add_new_document_type
                    conn = create_memory_database()
                    
                    # Get the original fields from the JSON (for registry matching)
                    all_fields = json_data.get('fields', [])
                    
                    registry_updated = add_new_document_type(
                        conn,
                        document_type,
                        document_type_code,
                        all_fields,  # Use original field names for registry matching
                        True,  # reuse_regularly = True (assume all are reusable)
                        response_text  # Use the full response as description
                    )
                    
                    if registry_updated:
                        print(f"✅ Document type '{document_type}' added to registry")
                    else:
                        print(f"⚠️  Failed to add document type to registry")
                        
                    conn.close()
                    
                except Exception as e:
                    print(f"⚠️  Registry update failed: {e}")
                    # Continue even if registry update fails
                
            elif field_name == "analysis_complete":
                json_data[field_name] = True
            
            # Update conversation history
            if "conversation_history" not in json_data:
                json_data["conversation_history"] = []
            
            json_data["conversation_history"].append({
                "step": conversation_step,
                "question": current_step["question"],
                "user_response": user_response,
                "timestamp": datetime.now().isoformat()
            })
            
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
                # After step 2, show step 3 question
                next_step = 3
                current_question = conversation_flow[2]["question"]
                conversation_status = "in_progress"
            elif conversation_step == 3:
                # After step 3, complete
                next_step = "complete"
                current_question = f"Perfect! I've classified this as a {json_data.get('document_type', 'document')} ({json_data.get('document_type_code', 'DOC')}). The document is now ready for DuckDB processing and SQL queries."
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
                            
                            # Generate safe table name
                            timestamp_short = json_data.get('upload_timestamp', '').replace('-', '').replace(':', '').replace(' ', '')
                            
                            # Create a safe table name from document_type
                            document_type = json_data.get('document_type', '')
                            if document_type and document_type != "New":
                                # Use first 2-3 words of document type, sanitized
                                words = document_type.split()[:3]
                                safe_type = '_'.join(words).lower()
                                safe_type = re.sub(r'[^a-zA-Z0-9_]', '_', safe_type)
                            else:
                                # Fallback to generic name
                                safe_type = "excel_data"
                            
                            # Ensure table name starts with letter and is valid
                            if safe_type and safe_type[0].isdigit():
                                safe_type = 'tbl_' + safe_type
                            
                            duckdb_table_name = f"{safe_type}_{timestamp_short}"
                            
                            # Final validation - ensure table name is valid
                            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', duckdb_table_name):
                                # If still invalid, use a completely safe fallback
                                duckdb_table_name = f"excel_data_{timestamp_short}"
                            
                            print(f"Generated table name: {duckdb_table_name}")
                            
                            # Create DuckDB connection and table
                            conn = create_memory_database()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
