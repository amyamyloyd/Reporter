from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Import Phase 1 modules
from excel_processor import extract_file_metadata, validate_excel_files
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
        
        # Extract metadata using Phase 1 module
        metadata = extract_file_metadata(files)
        
        # Create in-memory database for session (Phase 1 foundation)
        db_conn = create_memory_database()
        
        # Create JSON file for each uploaded file
        import json
        import os
        from datetime import datetime
        
        # Ensure the files directory exists
        os.makedirs("stored_queries/files", exist_ok=True)
        
        for file in validation["valid_files"]:
            file_metadata = metadata.get(file.filename, {})
            
            # Create unique filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            base_name = os.path.splitext(file.filename)[0]  # Remove .xlsx extension
            json_filename = f"{base_name}_{timestamp}.json"
            excel_filename = f"{base_name}_{timestamp}.xlsx"
            
            json_path = f"stored_queries/{json_filename}"
            excel_path = f"stored_queries/files/{excel_filename}"
            
            # Save the actual Excel file with timestamp
            with open(excel_path, 'wb') as f:
                # Read file content and write to disk
                content = await file.read()
                f.write(content)
                # Reset file pointer for later processing
                await file.seek(0)
            
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
            
            # Create JSON structure
            json_data = {
                "filename": excel_filename,  # Reference the saved Excel file
                "sheets": file_metadata.get("sheets", {}),
                "fields": all_fields,  # Original field names for display
                "normalized_fields": normalized_fields,  # Clean field names for DuckDB
                "record_count": sum(sheet.get("row_count", 0) for sheet in file_metadata.get("sheets", {}).values()),
                "upload_timestamp": timestamp,
                "file_size": file.size,
                "content_type": file.content_type
            }
            
            # Save JSON file
            with open(json_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            print(f"Saved Excel file: {excel_path}")
            print(f"Created JSON file: {json_path}")
            
            # NEW: DuckDB Integration - Create table and check document type
            try:
                # Load Excel data into pandas DataFrame for DuckDB
                import pandas as pd
                df = pd.read_excel(excel_path, engine='openpyxl')
                
                # Apply normalized column names for DuckDB compatibility
                if normalized_fields and len(normalized_fields) == len(df.columns):
                    df.columns = normalized_fields
                    print(f"Applied normalized column names for DuckDB compatibility")
                
                print(f"Loaded Excel data: {df.shape[0]} rows, {df.shape[1]} columns")
                
                # Check document registry for matching field patterns using normalized fields
                from duckdb_manager import check_document_type_by_fields
                doc_type_info = check_document_type_by_fields(db_conn, normalized_fields)
                
                # Determine document type and table naming
                if doc_type_info:
                    # Found matching document type
                    document_type = doc_type_info["document_type"]
                    document_type_code = doc_type_info["document_type_code"]
                    is_current_version = True  # This is the latest version
                    print(f"Matched existing document type: {document_type}")
                else:
                    # New document type
                    document_type = "New"
                    document_type_code = "new"
                    is_current_version = True
                    print(f"New document type detected - no pattern match found")
                    
                    # Step 3: Add new document to registry for future auto-detection
                    try:
                        from duckdb_manager import add_new_document_type
                        registry_updated = add_new_document_type(
                            db_conn,
                            "New Document",  # Generic name until user provides specific type
                            "new",           # Generic code until user provides specific code
                            normalized_fields,      # Store field pattern for future matching
                            False,           # reuse_regularly = False initially
                            "Document type to be determined by user during analysis"
                        )
                        
                        if registry_updated:
                            print(f"✅ New document added to registry for future auto-detection")
                        else:
                            print(f"⚠️  Failed to add new document to registry")
                            
                    except Exception as e:
                        print(f"⚠️  Registry update failed: {e}")
                        # Continue with upload even if registry update fails
                
                # Generate DuckDB table name with proper convention
                # Format: {type}_{timestamp}_{version}
                timestamp_short = timestamp.replace('-', '').replace(':', '')
                duckdb_table_name = f"{document_type_code.lower()}_{timestamp_short}"
                
                # Create DuckDB table
                from duckdb_manager import dataframe_to_table
                table_created = dataframe_to_table(db_conn, df, duckdb_table_name)
                
                if table_created:
                    print(f"✅ DuckDB table created: {duckdb_table_name}")
                    
                    # Extract data version from filename
                    from duckdb_manager import extract_data_version_from_filename
                    data_version = extract_data_version_from_filename(excel_filename)
                    
                    # Update JSON with DuckDB metadata
                    json_data.update({
                        "duckdb_table_name": duckdb_table_name,
                        "duckdb_loaded": True,
                        "data_version": data_version,
                        "document_type": document_type,
                        "document_type_code": document_type_code,
                        "is_current_version": is_current_version
                    })
                    
                    # Save updated JSON with DuckDB metadata
                    with open(json_path, 'w') as f:
                        json.dump(json_data, f, indent=2)
                    
                    print(f"✅ JSON updated with DuckDB metadata")
                    
                else:
                    print(f"❌ Failed to create DuckDB table: {duckdb_table_name}")
                    # Still update JSON but mark as not loaded
                    json_data.update({
                        "duckdb_table_name": None,
                        "duckdb_loaded": False,
                        "data_version": None,
                        "document_type": document_type,
                        "document_type_code": document_type_code,
                        "is_current_version": is_current_version
                    })
                    
            except Exception as e:
                print(f"❌ DuckDB integration failed: {e}")
                # Update JSON with error state
                json_data.update({
                    "duckdb_table_name": None,
                    "duckdb_loaded": False,
                    "data_version": None,
                    "document_type": "New",
                    "document_type_code": "new",
                    "is_current_version": True,
                    "duckdb_error": str(e)
                })
                
                # Save updated JSON even with errors
                with open(json_path, 'w') as f:
                    json.dump(json_data, f, indent=2)
        
        # Return files array that frontend expects for AgentChat
        files_data = []
        for i, file in enumerate(validation["valid_files"]):
            file_metadata = metadata.get(file.filename, {})
            
            # Combine fields from all sheets for the frontend
            all_fields = []
            if "sheets" in file_metadata:
                for sheet_name, sheet_data in file_metadata["sheets"].items():
                    if "fields" in sheet_data:
                        all_fields.extend(sheet_data["fields"])
                # Remove duplicates while preserving order
                all_fields = list(dict.fromkeys(all_fields))
            
            # Create JSON filename for this file
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            base_name = os.path.splitext(file.filename)[0]
            json_filename = f"{base_name}_{timestamp}.json"
            
            files_data.append({
                "name": file.filename,  # Frontend expects 'name' property
                "size": file.size,
                "content_type": file.content_type,
                "fields": all_fields,  # Combined fields from all sheets
                "sheets": file_metadata.get("sheets", []),
                "file_index": i,
                "json_filename": json_filename  # Include JSON filename for ChatAgent
            })
        
        return {
            "success": True,
            "message": f"Successfully processed {len(validation['valid_files'])} files",
            "files": files_data,  # This is what AgentChat expects
            "validation": validation,
            "metadata": metadata,
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
        
        # Initialize conversation flow
        conversation_flow = [
            {
                "step": 1,
                "question": f"Per my analysis, this file includes {', '.join(json_data.get('fields', []))} with {json_data.get('record_count', 0)} records. Is that correct?",
                "field": "user_confirmation",
                "next_step": 2
            },
            {
                "step": 2,
                "question": "Please provide a brief description of this document and its purpose",
                "field": "user_description",
                "next_step": 3
            },
            {
                "step": 3,
                "question": "Agent will confirm understanding and complete analysis",
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
            elif field_name == "user_description":
                json_data[field_name] = user_response.strip()
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
                current_question = "Analysis complete! Ready for next phase."
                conversation_status = "completed"
                json_data["analysis_complete"] = True
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
