from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import os
import json
import re
import logging
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import duckdb
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Phase 1 modules
from excel_processor import extract_file_metadata_from_saved_file, validate_excel_files
from duckdb_manager import create_persistent_database

# Import Phase 2A modules
from agents.file_analyzer import analyze_single_file

# Import new utility modules for /query endpoint
from utils.json_store import load_metadata, append_query_to_metadata, append_report_to_metadata
from utils.duckdb_manager import save_query, save_report, ensure_all_tables_exist

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

@app.get("/tables")
async def view_tables():
    """Display doc_registry, saved_queries, and saved_reports in HTML tables"""
    try:
        # Create database connection
        conn = create_persistent_database()
        
        # Ensure all tables exist
        ensure_all_tables_exist()
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Excel Reporting - Database Tables</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                h1 { color: #333; text-align: center; }
                h2 { color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f8f9fa; font-weight: bold; color: #333; }
                tr:hover { background-color: #f5f5f5; }
                .count { background-color: #e3f2fd; padding: 5px 10px; border-radius: 3px; font-weight: bold; }
                .refresh { text-align: center; margin: 20px 0; }
                .refresh a { background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
                .refresh a:hover { background-color: #0056b3; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🗄️ AI Excel Reporting - Database Tables</h1>
                <div class="refresh">
                    <a href="/tables">🔄 Refresh</a>
                </div>
        """
        
        # Get doc_registry data
        try:
            doc_registry_result = conn.execute("SELECT * FROM doc_registry ORDER BY document_type, latest_version DESC").fetchall()
            doc_registry_columns = [desc[0] for desc in conn.execute("PRAGMA table_info(doc_registry)").fetchall()]
            
            html_content += f"""
                <h2>📋 Document Registry <span class="count">{len(doc_registry_result)} records</span></h2>
                <table>
                    <thead>
                        <tr>
            """
            for col in doc_registry_columns:
                html_content += f"<th>{col}</th>"
            html_content += """
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for row in doc_registry_result:
                html_content += "<tr>"
                for value in row:
                    html_content += f"<td>{value if value is not None else ''}</td>"
                html_content += "</tr>"
            
            html_content += """
                    </tbody>
                </table>
            """
        except Exception as e:
            html_content += f"<p>❌ Error loading doc_registry: {e}</p>"
        
        # Get saved_queries data
        try:
            saved_queries_result = conn.execute("SELECT * FROM saved_queries ORDER BY created_date DESC").fetchall()
            saved_queries_columns = [desc[0] for desc in conn.execute("PRAGMA table_info(saved_queries)").fetchall()]
            
            html_content += f"""
                <h2>🔍 Saved Queries <span class="count">{len(saved_queries_result)} records</span></h2>
                <table>
                    <thead>
                        <tr>
            """
            for col in saved_queries_columns:
                html_content += f"<th>{col}</th>"
            html_content += """
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for row in saved_queries_result:
                html_content += "<tr>"
                for i, value in enumerate(row):
                    # Truncate long SQL queries for display
                    if saved_queries_columns[i] == 'sql' and value and len(str(value)) > 100:
                        html_content += f"<td title='{value}'>{str(value)[:100]}...</td>"
                    else:
                        html_content += f"<td>{value if value is not None else ''}</td>"
                html_content += "</tr>"
            
            html_content += """
                    </tbody>
                </table>
            """
        except Exception as e:
            html_content += f"<p>❌ Error loading saved_queries: {e}</p>"
        
        # Get saved_reports data
        try:
            saved_reports_result = conn.execute("SELECT * FROM saved_reports ORDER BY created_date DESC").fetchall()
            saved_reports_columns = [desc[0] for desc in conn.execute("PRAGMA table_info(saved_reports)").fetchall()]
            
            html_content += f"""
                <h2>📊 Saved Reports <span class="count">{len(saved_reports_result)} records</span></h2>
                <table>
                    <thead>
                        <tr>
            """
            for col in saved_reports_columns:
                html_content += f"<th>{col}</th>"
            html_content += """
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for row in saved_reports_result:
                html_content += "<tr>"
                for value in row:
                    html_content += f"<td>{value if value is not None else ''}</td>"
                html_content += "</tr>"
            
            html_content += """
                    </tbody>
                </table>
            """
        except Exception as e:
            html_content += f"<p>❌ Error loading saved_reports: {e}</p>"
        
        # Close HTML
        html_content += """
            </div>
        </body>
        </html>
        """
        
        conn.close()
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>❌ Error Loading Tables</h1>
            <p>{str(e)}</p>
            <a href="/tables">🔄 Try Again</a>
        </body>
        </html>
        """
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=error_html, status_code=500)

@app.get("/download-excel/{filename}")
async def download_excel(filename: str):
    """Download Excel file generated from query results"""
    try:
        import os
        from fastapi.responses import FileResponse
        
        # Security check - only allow alphanumeric, hyphens, underscores, and dots
        if not re.match(r'^[a-zA-Z0-9._-]+\.xlsx$', filename):
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        filepath = os.path.join("stored_queries", "excel_exports", filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading Excel file {filename}: {e}")
        raise HTTPException(status_code=500, detail="Download failed")

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
            
            # Get duckdb_table_name from the JSON metadata
            duckdb_table_name = None
            if json_filename:
                json_path = f"stored_queries/{json_filename}"
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r') as f:
                            json_data = json.load(f)
                            duckdb_table_name = json_data.get("duckdb_table_name")
                    except Exception as e:
                        print(f"Warning: Could not read JSON metadata for {json_filename}: {e}")
            
            files_data.append({
                "name": file.filename,  # Frontend expects 'name' property
                "size": file.size,
                "content_type": file.content_type,
                "fields": all_fields,  # Combined fields from all sheets
                "sheets": file_metadata.get("sheets", {}) if file_metadata else {},
                "file_index": i,
                "json_filename": json_filename,  # Include JSON filename for ChatAgent
                "duckdb_table_name": duckdb_table_name  # Include DuckDB table name for AutoGen
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

# Phase 3: AutoGen Agent System Endpoints

@app.post("/autogen-chat")
async def autogen_chat_endpoint(request: Dict[str, Any]):
    """
    AutoGen Agent System - Main conversation endpoint
    
    This endpoint processes user messages through the complete AutoGen agent pipeline:
    ChatAgent -> OrchestrationAgent -> Target Agent (Query/Report/Upload/Memory)
    
    Args:
        request: Dict containing:
            - user_input: User's natural language message
            - localStorage_context: Context from frontend localStorage
            
    Returns:
        Dict with agent response, routing info, and results
    """
    try:
        # Import the agent orchestrator
        from agents.agent_orchestrator import get_agent_orchestrator
        
        # Extract request data
        user_input = request.get("user_input", "")
        localStorage_context = request.get("localStorage_context", {})
        
        if not user_input.strip():
            raise HTTPException(status_code=400, detail="user_input is required")
        
        # Get the agent orchestrator
        orchestrator = get_agent_orchestrator()
        
        # Process the user message through the agent pipeline
        result = await orchestrator.process_user_message(user_input, localStorage_context)
        
        # Return the complete result
        return {
            "success": result.get("success", False),
            "data": result,
            "message": "AutoGen agent processing completed"
        }
        
    except Exception as e:
        logger.error(f"AutoGen chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"AutoGen processing failed: {str(e)}")

@app.get("/autogen-status")
async def autogen_status_endpoint():
    """
    Get status of all AutoGen agents
    
    Returns:
        Dict with status information for all agents
    """
    try:
        # Import the agent orchestrator
        from agents.agent_orchestrator import get_agent_orchestrator
        
        # Get the agent orchestrator
        orchestrator = get_agent_orchestrator()
        
        # Get agent status
        status = orchestrator.get_agent_status()
        
        return {
            "success": True,
            "data": status,
            "message": "AutoGen agent status retrieved"
        }
        
    except Exception as e:
        logger.error(f"AutoGen status endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"AutoGen status check failed: {str(e)}")

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

@app.post("/query")
async def query_endpoint(request: Dict[str, Any]):
    """
    Query endpoint - Natural language to SQL with DuckDB execution
    
    This endpoint receives a query in natural language or structured input,
    generates SQL using LLM, executes via DuckDB, and returns results.
    
    Input format (exactly as specified):
    {
        "doc_id": "hospital_ledger_fy2024_001",
        "query_text": "How much did we spend on Vendor X in Q2?",
        "schema": ["Vendor", "Date", "Amount"],
        "metadata": {"record_count": 1200, "created": "2024-01-01"},
        "datetime_context": {"now": "2025-09-02", "current_quarter": "Q3", "last_quarter": "Q2"}
    }
    
    Output format (exactly as specified):
    {
        "sql": "SELECT SUM(Amount) FROM hospital_ledger_fy2024_001 WHERE Vendor = 'Vendor X' AND Quarter = 'Q2'",
        "rows": [[124000.50]],
        "columns": ["Total Amount"],
        "summary": "We spent $124,000.50 on Vendor X in Q2."
    }
    """
    try:
        # Extract and validate required fields
        doc_id = request.get("doc_id")
        query_text = request.get("query_text")
        schema = request.get("schema", [])
        metadata = request.get("metadata", {})
        datetime_context = request.get("datetime_context", {})
        
        # Validate required fields
        if not doc_id:
            raise HTTPException(status_code=400, detail="Missing required field: doc_id")
        if not query_text:
            raise HTTPException(status_code=400, detail="Missing required field: query_text")
        
        logger.info(f"Processing query for doc_id: {doc_id}")
        logger.info(f"Query text: {query_text}")
        
        # Load document metadata to get table name and additional context
        doc_metadata = load_metadata(doc_id)
        if not doc_metadata:
            raise HTTPException(status_code=404, detail=f"Document metadata not found for doc_id: {doc_id}")
        
        # Get DuckDB table name from metadata
        duckdb_table_name = doc_metadata.get("duckdb_table_name")
        if not duckdb_table_name:
            raise HTTPException(status_code=400, detail=f"No DuckDB table found for doc_id: {doc_id}")
        
        logger.info(f"Using DuckDB table: {duckdb_table_name}")
        
        # Ensure all required tables exist
        ensure_all_tables_exist()
        
        # Create database connection
        conn = create_persistent_database()
        
        # Get actual table schema from DuckDB
        try:
            schema_result = conn.execute(f"DESCRIBE {duckdb_table_name}").fetchall()
            actual_schema = [col[0] for col in schema_result]
            logger.info(f"Actual table schema: {actual_schema}")
        except Exception as e:
            logger.error(f"Failed to get table schema: {e}")
            actual_schema = schema  # Fallback to provided schema
        
        # Generate SQL using LLM
        sql_query = await generate_sql_from_natural_language(
            query_text=query_text,
            table_name=duckdb_table_name,
            schema=actual_schema,
            metadata=metadata,
            datetime_context=datetime_context
        )
        
        if not sql_query:
            raise HTTPException(status_code=500, detail="Failed to generate SQL query")
        
        logger.info(f"Generated SQL: {sql_query}")
        
        # Execute SQL via DuckDB
        try:
            result = conn.execute(sql_query).fetchall()
            columns_result = conn.execute(sql_query).description
            
            # Extract column names
            columns = [col[0] for col in columns_result] if columns_result else []
            
            # Convert rows to list format
            rows = [list(row) for row in result]
            
            logger.info(f"Query executed successfully: {len(rows)} rows returned")
            
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise HTTPException(status_code=500, detail=f"SQL execution failed: {str(e)}")
        
        # Generate natural language summary using LLM
        summary = await generate_query_summary(
            query_text=query_text,
            sql_query=sql_query,
            rows=rows,
            columns=columns
        )
        
        # Auto-save query with fallback name "temp_query" (as specified)
        query_name = request.get("query_name", "temp_query")
        tags = request.get("tags", [])
        
        save_success = save_query(
            conn=conn,
            doc_id=doc_id,
            query_name=query_name,
            query_text=query_text,
            sql=sql_query,
            tags=tags,
            description=f"Auto-generated from: {query_text}"
        )
        
        if save_success:
            logger.info(f"Query saved successfully as: {query_name}")
        else:
            logger.warning(f"Failed to save query: {query_name}")
        
        # Append query to document metadata
        query_data = {
            "query_name": query_name,
            "query_text": query_text,
            "sql": sql_query,
            "tags": tags,
            "rows_returned": len(rows)
        }
        
        append_success = append_query_to_metadata(doc_id, query_data)
        if append_success:
            logger.info("Query appended to document metadata")
        else:
            logger.warning("Failed to append query to document metadata")
        
        # Close database connection
        conn.close()
        
        # Return results in exact format specified
        return {
            "sql": sql_query,
            "rows": rows,
            "columns": columns,
            "summary": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in query endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

async def generate_sql_from_natural_language(query_text: str, table_name: str, 
                                            schema: List[str], metadata: Dict[str, Any],
                                            datetime_context: Dict[str, str]) -> str:
    """
    Generate SQL query from natural language using LLM
    
    This function uses OpenAI to convert natural language queries into
    valid SQL that can be executed against the DuckDB table.
    
    Args:
        query_text: Natural language query
        table_name: Name of the DuckDB table
        schema: List of column names in the table
        metadata: Document metadata (record count, etc.)
        datetime_context: Current date/time context
        
    Returns:
        str: Generated SQL query
    """
    try:
        from openai import OpenAI
        import os
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create comprehensive system prompt for SQL generation
        system_prompt = f"""You are an expert SQL query generator for DuckDB databases.

Your task is to convert natural language queries into valid DuckDB SQL.

TABLE INFORMATION:
- Table name: {table_name}
- Columns: {', '.join(schema)}
- Record count: {metadata.get('record_count', 'unknown')}
- Document type: {metadata.get('document_type', 'unknown')}

DATETIME CONTEXT:
- Current date: {datetime_context.get('now', 'unknown')}
- Current quarter: {datetime_context.get('current_quarter', 'unknown')}
- Last quarter: {datetime_context.get('last_quarter', 'unknown')}

RULES:
1. Generate ONLY the SQL query - no explanations, no markdown, no code blocks
2. Use proper DuckDB syntax
3. Handle date/time queries using the datetime context
4. Use appropriate aggregation functions (SUM, COUNT, AVG, etc.)
5. Include proper WHERE clauses for filtering
6. Use column names exactly as provided in the schema
7. For date ranges, use the datetime context to determine quarters, months, etc.
8. Always include a LIMIT clause for large result sets (max 1000 rows)
9. CRITICAL: Quote ALL column names with double quotes if they contain spaces
10. Example: "Transaction Type" not Transaction Type
11. CRITICAL: Return ONLY the SQL query text, nothing else
12. Do NOT wrap the SQL in quotes, backticks, or any other formatting

EXAMPLES:
- "How much did we spend on Vendor X in Q2?" → "SELECT SUM(\"Amount\") FROM {table_name} WHERE \"Company Code\" = 'COMP001' LIMIT 1000"
- "Show me the total amount by transaction type" → "SELECT \"Transaction Type\", SUM(\"Amount\") as Total_Amount FROM {table_name} GROUP BY \"Transaction Type\" LIMIT 1000"
- "What's the average amount per transaction?" → "SELECT AVG(\"Amount\") as Average_Amount FROM {table_name} LIMIT 1000"

Generate SQL for this query:"""

        # Create user prompt
        user_prompt = f"Query: {query_text}"
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        # Extract SQL query from response
        sql_query = response.choices[0].message.content.strip()
        
        # Clean up the SQL query (remove any markdown formatting)
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        sql_query = sql_query.strip()
        
        # Remove any surrounding quotes that might wrap the entire SQL
        if sql_query.startswith('"') and sql_query.endswith('"'):
            sql_query = sql_query[1:-1]
        if sql_query.startswith("'") and sql_query.endswith("'"):
            sql_query = sql_query[1:-1]
        
        # Debug: Log the raw SQL before processing
        logger.info(f"Raw SQL from LLM: {repr(sql_query)}")
        
        # Fix DuckDB syntax: replace backticks with double quotes for column names
        sql_query = sql_query.replace("`", '"')
        
        # Debug: Log the processed SQL
        logger.info(f"Processed SQL: {repr(sql_query)}")
        
        logger.info(f"Generated SQL query: {sql_query}")
        return sql_query
        
    except Exception as e:
        logger.error(f"Failed to generate SQL from natural language: {e}")
        return None

async def generate_query_summary(query_text: str, sql_query: str, 
                               rows: List[List], columns: List[str]) -> str:
    """
    Generate natural language summary of query results using LLM
    
    This function uses OpenAI to create a human-readable summary of the
    query results in natural language.
    
    Args:
        query_text: Original natural language query
        sql_query: Generated SQL query
        rows: Query result rows
        columns: Column names
        
    Returns:
        str: Natural language summary of results
    """
    try:
        from openai import OpenAI
        import os
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Prepare result data for summary
        result_summary = f"Query returned {len(rows)} rows with columns: {', '.join(columns)}"
        
        # Include first few rows as examples (limit to avoid token limits)
        sample_rows = rows[:3] if len(rows) > 3 else rows
        if sample_rows:
            result_summary += f"\nSample results: {sample_rows}"
        
        # Create system prompt for summary generation
        system_prompt = """You are an expert at creating natural language summaries of database query results.

Your task is to create a concise, human-readable summary of query results that answers the original question.

RULES:
1. Be concise and direct
2. Include specific numbers and values from the results
3. Answer the original question clearly
4. Use natural language, not technical jargon
5. If no results, explain why
6. Keep summary under 100 words

EXAMPLES:
- If query was "How much did we spend on Vendor X in Q2?" and result is [[124000.50]]
  → "We spent $124,000.50 on Vendor X in Q2."
- If query was "Show me top vendors" and result is [["Vendor A", 50000], ["Vendor B", 30000]]
  → "The top vendors are Vendor A with $50,000 and Vendor B with $30,000."
- If no results: "No records found matching your criteria."

Create a summary for these results:"""

        # Create user prompt
        user_prompt = f"""Original question: {query_text}
SQL query: {sql_query}
{result_summary}"""
        
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
        
        # Extract summary from response
        summary = response.choices[0].message.content.strip()
        
        logger.info(f"Generated query summary: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate query summary: {e}")
        # Fallback summary
        return f"Query executed successfully and returned {len(rows)} rows."

@app.post("/report")
async def report_endpoint(request: Dict[str, Any]):
    """
    Report endpoint - Generate reports with filters, grouping, formatting
    
    This endpoint generates reports using filters, grouping, formatting, and natural language titles.
    Uses LLM to interpret vague report names and builds output using pandas + duckdb.
    
    Input format (exactly as specified):
    {
        "doc_id": "hospital_ledger_fy2024_001",
        "report_name": "Weekly Vendor Spend",
        "sql": "SELECT Week, SUM(Amount) FROM table WHERE vendor = 'Vendor X' GROUP BY Week",
        "filters": {"vendor": "Vendor X", "quarter": "Q2"},
        "group_by": ["Week"],
        "format": "chart",
        "output_type": "html"
    }
    
    Output: HTML, XLSX, or JSON based on output_type
    """
    try:
        # Extract and validate required fields
        doc_id = request.get("doc_id")
        report_name = request.get("report_name", "temp_report")  # Fallback name as specified
        sql_query = request.get("sql", "")  # SQL query to execute
        filters = request.get("filters", {})
        group_by = request.get("group_by", [])
        format_type = request.get("format", "table")
        output_type = request.get("output_type", "html")
        
        # Validate required fields
        if not doc_id:
            raise HTTPException(status_code=400, detail="Missing required field: doc_id")
        if not sql_query:
            raise HTTPException(status_code=400, detail="Missing required field: sql")
        
        logger.info(f"Processing report for doc_id: {doc_id}")
        logger.info(f"Report name: {report_name}")
        logger.info(f"Output type: {output_type}")
        
        # Load document metadata to get table name and additional context
        doc_metadata = load_metadata(doc_id)
        if not doc_metadata:
            raise HTTPException(status_code=404, detail=f"Document metadata not found for doc_id: {doc_id}")
        
        # Get DuckDB table name from metadata
        duckdb_table_name = doc_metadata.get("duckdb_table_name")
        if not duckdb_table_name:
            raise HTTPException(status_code=400, detail=f"No DuckDB table found for doc_id: {doc_id}")
        
        logger.info(f"Using DuckDB table: {duckdb_table_name}")
        
        # Ensure all required tables exist
        ensure_all_tables_exist()
        
        # Create database connection
        conn = create_persistent_database()
        
        # Get actual table schema from DuckDB
        try:
            schema_result = conn.execute(f"DESCRIBE {duckdb_table_name}").fetchall()
            actual_schema = [col[0] for col in schema_result]
            logger.info(f"Actual table schema: {actual_schema}")
        except Exception as e:
            logger.error(f"Failed to get table schema: {e}")
            actual_schema = doc_metadata.get("fields", [])  # Fallback to metadata fields
        
        # Create report configuration from provided SQL
        report_config = {
            "sql": sql_query,
            "description": f"Report: {report_name}",
            "chart": "bar" if format_type == "chart" else "",
            "table_name": duckdb_table_name  # Pass table name for file naming
        }
        
        logger.info(f"Using provided SQL: {sql_query}")
        
        # Generate report using report_builder
        from utils.report_builder import build_report
        
        report_result = await build_report(
            conn=conn,
            table_name=duckdb_table_name,
            report_config=report_config,
            output_type=output_type
        )
        
        if not report_result:
            raise HTTPException(status_code=500, detail="Failed to build report")
        
        # Auto-save report with fallback name "temp_report" (as specified)
        save_success = save_report(
            conn=conn,
            doc_id=doc_id,
            report_name=report_name,
            sql=sql_query,
            filters=filters,
            group_by=group_by,
            format=format_type,
            chart=report_config.get("chart", ""),
            output_type=output_type,
            description=report_config.get("description", f"Report: {report_name}")
        )
        
        if save_success:
            logger.info(f"Report saved successfully as: {report_name}")
        else:
            logger.warning(f"Failed to save report: {report_name}")
        
        # Append report to document metadata
        report_data = {
            "report_name": report_name,
            "filters": filters,
            "group_by": group_by,
            "format": format_type,
            "output_type": output_type,
            "sql": sql_query,
            "chart": report_config.get("chart", "")
        }
        
        append_success = append_report_to_metadata(doc_id, report_data)
        if append_success:
            logger.info("Report appended to document metadata")
        else:
            logger.warning("Failed to append report to document metadata")
        
        # Close database connection
        conn.close()
        
        # Return comprehensive results for next agent processing
        base_result = {
            "success": True,
            "doc_id": doc_id,
            "duckdb_table_name": duckdb_table_name,
            "report_name": report_name,
            "sql": sql_query,
            "filters": filters,
            "group_by": group_by,
            "format": format_type,
            "output_type": output_type,
            "chart": report_config.get("chart", ""),
            "description": report_config.get("description", f"Report: {report_name}"),
            "row_count": report_result.get("row_count", 0),
            "column_count": report_result.get("column_count", 0),
            "summary": report_result.get("summary", f"Generated {report_name} report"),
            "generated_timestamp": datetime.now().isoformat(),
            "saved_to_db": save_success,
            "saved_to_metadata": append_success
        }
        
        # Add output-specific data
        if output_type == "html":
            base_result.update({
                "content": report_result.get("html", ""),
                "content_type": "html"
            })
        elif output_type == "xlsx":
            base_result.update({
                "download_url": report_result.get("download_url", ""),
                "filename": report_result.get("filename", f"{duckdb_table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"),
                "filepath": report_result.get("filepath", ""),
                "content_type": "xlsx"
            })
        elif output_type == "json":
            base_result.update({
                "data": report_result.get("data", {}),
                "content_type": "json"
            })
        else:
            # Default to HTML
            base_result.update({
                "content": report_result.get("html", ""),
                "content_type": "html"
            })
        
        return base_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in report endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Report processing failed: {str(e)}")

@app.post("/save_query")
async def save_query_endpoint(request: Dict[str, Any]):
    """
    Save query endpoint - Persist queries to DuckDB and .json
    
    This endpoint saves query information to both the DuckDB saved_queries table
    and appends it to the document's JSON metadata file.
    
    Input format (exactly as specified):
    {
        "doc_id": "hospital_ledger_fy2024_001",
        "query_text": "How much did we spend on Vendor X in Q2?",
        "sql": "SELECT SUM(Amount) FROM hospital_ledger_fy2024_001 WHERE Vendor = 'Vendor X' AND Quarter = 'Q2'",
        "query_name": "Quarterly Vendor Spend",
        "tags": ["vendor", "q2", "spending"]
    }
    
    Output: Success confirmation with saved query details
    """
    try:
        # Extract and validate required fields
        doc_id = request.get("doc_id")
        query_text = request.get("query_text")
        sql = request.get("sql")
        query_name = request.get("query_name")
        tags = request.get("tags", [])
        
        # Validate required fields
        if not doc_id:
            raise HTTPException(status_code=400, detail="Missing required field: doc_id")
        if not query_text:
            raise HTTPException(status_code=400, detail="Missing required field: query_text")
        if not sql:
            raise HTTPException(status_code=400, detail="Missing required field: sql")
        if not query_name:
            raise HTTPException(status_code=400, detail="Missing required field: query_name")
        
        logger.info(f"Saving query for doc_id: {doc_id}")
        logger.info(f"Query name: {query_name}")
        
        # Verify document metadata exists
        doc_metadata = load_metadata(doc_id)
        if not doc_metadata:
            raise HTTPException(status_code=404, detail=f"Document metadata not found for doc_id: {doc_id}")
        
        # Ensure all required tables exist
        ensure_all_tables_exist()
        
        # Create database connection
        conn = create_persistent_database()
        
        # Save query to DuckDB saved_queries table
        save_success = save_query(
            conn=conn,
            doc_id=doc_id,
            query_name=query_name,
            query_text=query_text,
            sql=sql,
            tags=tags,
            description=f"Saved query: {query_name}"
        )
        
        if not save_success:
            conn.close()
            raise HTTPException(status_code=500, detail="Failed to save query to DuckDB")
        
        logger.info(f"Query saved successfully to DuckDB: {query_name}")
        
        # Append query to document metadata JSON
        query_data = {
            "query_name": query_name,
            "query_text": query_text,
            "sql": sql,
            "tags": tags,
            "saved_timestamp": datetime.now().isoformat()
        }
        
        append_success = append_query_to_metadata(doc_id, query_data)
        if not append_success:
            logger.warning(f"Failed to append query to document metadata for doc_id: {doc_id}")
        
        # Close database connection
        conn.close()
        
        # Return success response
        return {
            "success": True,
            "message": f"Query '{query_name}' saved successfully",
            "doc_id": doc_id,
            "query_name": query_name,
            "query_text": query_text,
            "sql": sql,
            "tags": tags,
            "saved_to_db": save_success,
            "saved_to_metadata": append_success,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in save_query endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Save query processing failed: {str(e)}")

@app.post("/save_report")
async def save_report_endpoint(request: Dict[str, Any]):
    """
    Save report endpoint - Persist reports to DuckDB and .json
    
    This endpoint saves report information to both the DuckDB saved_reports table
    and appends it to the document's JSON metadata file.
    
    Input format (exactly as specified):
    {
        "doc_id": "hospital_ledger_fy2024_001",
        "report_name": "Weekly Vendor Spend",
        "sql": "SELECT Week, SUM(Amount) FROM hospital_ledger_fy2024_001 GROUP BY Week",
        "filters": {"vendor": "Vendor X", "quarter": "Q2"},
        "group_by": ["Week"],
        "format": "chart",
        "chart": "bar",
        "description": "Summarizes weekly spending by vendor."
    }
    
    Output: Success confirmation with saved report details
    """
    try:
        # Extract and validate required fields
        doc_id = request.get("doc_id")
        report_name = request.get("report_name")
        sql = request.get("sql", "")  # SQL is optional for save_report
        filters = request.get("filters", {})
        group_by = request.get("group_by", [])
        format_type = request.get("format", "table")
        chart = request.get("chart", "")
        description = request.get("description", "")
        
        # Validate required fields
        if not doc_id:
            raise HTTPException(status_code=400, detail="Missing required field: doc_id")
        if not report_name:
            raise HTTPException(status_code=400, detail="Missing required field: report_name")
        
        logger.info(f"Saving report for doc_id: {doc_id}")
        logger.info(f"Report name: {report_name}")
        
        # Verify document metadata exists
        doc_metadata = load_metadata(doc_id)
        if not doc_metadata:
            raise HTTPException(status_code=404, detail=f"Document metadata not found for doc_id: {doc_id}")
        
        # Ensure all required tables exist
        ensure_all_tables_exist()
        
        # Create database connection
        conn = create_persistent_database()
        
        # Save report to DuckDB saved_reports table
        save_success = save_report(
            conn=conn,
            doc_id=doc_id,
            report_name=report_name,
            sql=sql,
            filters=filters,
            group_by=group_by,
            format=format_type,
            chart=chart,
            output_type="html",  # Default output type for saved reports
            description=description
        )
        
        if not save_success:
            conn.close()
            raise HTTPException(status_code=500, detail="Failed to save report to DuckDB")
        
        logger.info(f"Report saved successfully to DuckDB: {report_name}")
        
        # Append report to document metadata JSON
        report_data = {
            "report_name": report_name,
            "sql": sql,
            "filters": filters,
            "group_by": group_by,
            "format": format_type,
            "chart": chart,
            "description": description,
            "saved_timestamp": datetime.now().isoformat()
        }
        
        append_success = append_report_to_metadata(doc_id, report_data)
        if not append_success:
            logger.warning(f"Failed to append report to document metadata for doc_id: {doc_id}")
        
        # Close database connection
        conn.close()
        
        # Return success response
        return {
            "success": True,
            "message": f"Report '{report_name}' saved successfully",
            "doc_id": doc_id,
            "report_name": report_name,
            "sql": sql,
            "filters": filters,
            "group_by": group_by,
            "format": format_type,
            "chart": chart,
            "description": description,
            "saved_to_db": save_success,
            "saved_to_metadata": append_success,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in save_report endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Save report processing failed: {str(e)}")

@app.get("/saved_queries")
async def get_saved_queries_endpoint(doc_id: str = None, doc_ids: str = None):
    """
    Get saved queries endpoint - Retrieve saved queries for navigation
    
    This endpoint retrieves saved queries for the frontend navigation system.
    Supports both single doc_id and multiple doc_ids for multi-document sessions.
    
    Query Parameters:
    - doc_id: Single document ID (string)
    - doc_ids: Comma-separated list of document IDs (string)
    
    Returns:
    - List of saved queries with navigation data
    """
    try:
        # Parse doc_ids parameter if provided
        doc_id_list = []
        if doc_id:
            doc_id_list.append(doc_id)
        elif doc_ids:
            # Split comma-separated doc_ids
            doc_id_list = [id.strip() for id in doc_ids.split(',') if id.strip()]
        
        if not doc_id_list:
            raise HTTPException(status_code=400, detail="Missing required parameter: doc_id or doc_ids")
        
        logger.info(f"Retrieving saved queries for doc_ids: {doc_id_list}")
        
        # Ensure all required tables exist
        ensure_all_tables_exist()
        
        # Create database connection
        conn = create_persistent_database()
        
        # Get saved queries using the utility function
        from utils.duckdb_manager import get_saved_queries
        
        if len(doc_id_list) == 1:
            queries = get_saved_queries(conn, doc_id=doc_id_list[0])
        else:
            queries = get_saved_queries(conn, doc_ids=doc_id_list)
        
        # Close database connection
        conn.close()
        
        # Return navigation-focused response
        return {
            "success": True,
            "message": f"Retrieved {len(queries)} saved queries",
            "doc_ids": doc_id_list,
            "queries": queries,
            "count": len(queries)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_saved_queries endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve saved queries: {str(e)}")

@app.get("/saved_reports")
async def get_saved_reports_endpoint(doc_id: str = None, doc_ids: str = None):
    """
    Get saved reports endpoint - Retrieve saved reports for navigation
    
    This endpoint retrieves saved reports for the frontend navigation system.
    Supports both single doc_id and multiple doc_ids for multi-document sessions.
    
    Query Parameters:
    - doc_id: Single document ID (string)
    - doc_ids: Comma-separated list of document IDs (string)
    
    Returns:
    - List of saved reports with navigation data
    """
    try:
        # Parse doc_ids parameter if provided
        doc_id_list = []
        if doc_id:
            doc_id_list.append(doc_id)
        elif doc_ids:
            # Split comma-separated doc_ids
            doc_id_list = [id.strip() for id in doc_ids.split(',') if id.strip()]
        
        if not doc_id_list:
            raise HTTPException(status_code=400, detail="Missing required parameter: doc_id or doc_ids")
        
        logger.info(f"Retrieving saved reports for doc_ids: {doc_id_list}")
        
        # Ensure all required tables exist
        ensure_all_tables_exist()
        
        # Create database connection
        conn = create_persistent_database()
        
        # Get saved reports using the utility function
        from utils.duckdb_manager import get_saved_reports
        
        if len(doc_id_list) == 1:
            reports = get_saved_reports(conn, doc_id=doc_id_list[0])
        else:
            reports = get_saved_reports(conn, doc_ids=doc_id_list)
        
        # Close database connection
        conn.close()
        
        # Return navigation-focused response
        return {
            "success": True,
            "message": f"Retrieved {len(reports)} saved reports",
            "doc_ids": doc_id_list,
            "reports": reports,
            "count": len(reports)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_saved_reports endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve saved reports: {str(e)}")

async def interpret_report_name(report_name: str, table_name: str, schema: List[str],
                              filters: Dict[str, Any], group_by: List[str], 
                              format_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interpret vague report name using LLM to determine logic and fields
    
    This function uses OpenAI to interpret vague report titles and determine
    the appropriate SQL logic, grouping, and formatting for the report.
    
    Args:
        report_name: Natural language report name
        table_name: Name of the DuckDB table
        schema: List of column names in the table
        filters: Dictionary of filters to apply
        group_by: List of fields to group by
        format_type: Report format (table, chart, etc.)
        metadata: Document metadata
        
    Returns:
        Dict[str, Any]: Interpreted report configuration
    """
    try:
        from openai import OpenAI
        import os
        
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create comprehensive system prompt for report interpretation
        system_prompt = f"""You are an expert at interpreting vague report names and determining appropriate SQL logic.

Your task is to analyze a report name and determine the appropriate SQL query, grouping, and formatting.

TABLE INFORMATION:
- Table name: {table_name}
- Columns: {', '.join(schema)}
- Record count: {metadata.get('record_count', 'unknown')}
- Document type: {metadata.get('document_type', 'unknown')}

CURRENT FILTERS: {filters}
CURRENT GROUP BY: {group_by}
FORMAT TYPE: {format_type}

RULES:
1. Generate a JSON response with these exact fields:
   - "sql": The SQL query to generate the report
   - "description": Clear description of what the report shows
   - "chart": Chart type if format is "chart" (bar, line, pie, etc.)
   - "group_by_fields": Fields to group by (if not already specified)
   - "filters": Additional filters to apply (if not already specified)

2. Use proper DuckDB syntax
3. Quote ALL column names with double quotes if they contain spaces
4. Include appropriate aggregation functions (SUM, COUNT, AVG, etc.)
5. For date-based reports, use appropriate date functions
6. Always include a LIMIT clause for large result sets (max 1000 rows)

EXAMPLES:
- "Weekly Vendor Spend" → Group by week, sum amounts, show vendor breakdown
- "Top 10 Customers" → Order by amount descending, limit 10
- "Monthly Trends" → Group by month, show trend over time
- "Vendor Performance" → Group by vendor, show key metrics

Generate configuration for this report:"""

        # Create user prompt
        user_prompt = f"Report name: {report_name}"
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        # Extract response content
        ai_response = response.choices[0].message.content.strip()
        
        # Parse JSON response
        try:
            import json
            interpreted_config = json.loads(ai_response)
            
            # Validate required fields
            required_fields = ["sql", "description"]
            for field in required_fields:
                if field not in interpreted_config:
                    raise ValueError(f"Missing required field: {field}")
            
            # Fix DuckDB syntax: replace backticks with double quotes for column names
            sql_query = interpreted_config["sql"].replace("`", '"')
            interpreted_config["sql"] = sql_query
            
            logger.info(f"Interpreted report configuration: {interpreted_config}")
            return interpreted_config
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"AI Response: {ai_response}")
            
            # Fallback: create basic configuration
            fallback_sql = f"SELECT * FROM {table_name} LIMIT 1000"
            if group_by:
                # Simple aggregation if group_by is specified
                quoted_cols = [f'"{col}"' for col in group_by]
                fallback_sql = f"SELECT {', '.join(quoted_cols)}, COUNT(*) as count FROM {table_name} GROUP BY {', '.join(quoted_cols)} LIMIT 1000"
            
            return {
                "sql": fallback_sql,
                "description": f"Basic report for {report_name}",
                "chart": "bar" if format_type == "chart" else "",
                "group_by_fields": group_by,
                "filters": filters
            }
        
    except Exception as e:
        logger.error(f"Failed to interpret report name: {e}")
        return None

@app.get("/execute_query/{query_name}")
async def execute_query_endpoint(query_name: str):
    """
    Execute saved query endpoint - Run saved queries by name
    
    Supports both frontend click-to-run and agent programmatic execution.
    Updates usage statistics and returns results in same format as /query endpoint.
    """
    try:
        # Validate query_name
        if not query_name or not query_name.strip():
            raise HTTPException(status_code=400, detail="Invalid query_name. Must be non-empty string.")
        
        # Ensure database tables exist
        ensure_all_tables_exist()
        conn = create_persistent_database()
        
        # Look up query directly in saved_queries table
        query_result = conn.execute("""
            SELECT id, doc_id, query_name, sql, query_text, tags, 
                   created_date, use_count, last_used
            FROM saved_queries 
            WHERE query_name = ?
        """, [query_name.strip()]).fetchone()
        
        if not query_result:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Query with name '{query_name}' not found")
        
        # Extract query information
        query_id = query_result[0]
        doc_id = query_result[1]
        sql_query = query_result[3]
        
        logger.info(f"Executing saved query: {query_name} (ID: {query_id})")
        
        # Load JSON metadata to get correct table name
        from utils.json_store import load_metadata
        doc_metadata = load_metadata(doc_id)
        if doc_metadata and "duckdb_table_name" in doc_metadata:
            correct_table_name = doc_metadata["duckdb_table_name"]
            # Fix the SQL query to use the correct table name
            import re
            # Find the table name in the SQL (after FROM keyword)
            sql_query = re.sub(r'FROM\s+\w+', f'FROM {correct_table_name}', sql_query, flags=re.IGNORECASE)
            logger.info(f"Corrected SQL to use table: {correct_table_name}")
        else:
            logger.warning(f"Could not load metadata for doc_id: {doc_id}")
        
        # Execute the SQL query via DuckDB
        try:
            # Execute the query
            result = conn.execute(sql_query).fetchall()
            columns = [desc[0] for desc in conn.description] if conn.description else []
            
            # Convert result to list of lists for JSON serialization
            rows = [list(row) for row in result]
            
            # Simple summary
            summary = f"Executed query '{query_name}' and returned {len(rows)} rows"
            
            # Update usage statistics directly
            conn.execute("""
                UPDATE saved_queries 
                SET use_count = COALESCE(use_count, 0) + 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            """, [query_id])
            
            conn.close()
            
            # Return results in same format as /query endpoint
            return {
                "success": True,
                "message": f"Successfully executed query: {query_name}",
                "query_id": query_id,
                "query_name": query_name,
                "sql": sql_query,
                "rows": rows,
                "columns": columns,
                "summary": summary,
                "execution_time": datetime.now().isoformat(),
                "doc_id": doc_id,
                "row_count": len(rows)
            }
            
        except Exception as sql_error:
            conn.close()
            logger.error(f"SQL execution error for query {query_name}: {sql_error}")
            raise HTTPException(status_code=500, detail=f"SQL execution failed: {str(sql_error)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in execute_query endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

@app.get("/execute_report/{report_name}")
async def execute_report_endpoint(report_name: str):
    """
    Execute saved report endpoint - Run saved reports by name
    
    Supports both frontend click-to-run and agent programmatic execution.
    Updates usage statistics and returns results in same format as /report endpoint.
    """
    try:
        # Validate report_name
        if not report_name or not report_name.strip():
            raise HTTPException(status_code=400, detail="Invalid report_name. Must be non-empty string.")
        
        # Ensure database tables exist
        ensure_all_tables_exist()
        conn = create_persistent_database()
        
        # Look up report directly in saved_reports table
        report_result = conn.execute("""
            SELECT id, doc_id, report_name, sql, filters, group_by, 
                   format, chart, output_type, description, created_date,
                   generation_count, last_generated
            FROM saved_reports 
            WHERE report_name = ?
        """, [report_name.strip()]).fetchone()
        
        if not report_result:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Report with name '{report_name}' not found")
        
        # Extract report information
        report_id = report_result[0]
        doc_id = report_result[1]
        sql_query = report_result[3]
        filters = report_result[4]
        group_by = report_result[5]
        format_type = report_result[6]
        chart = report_result[7]
        output_type = report_result[8]
        description = report_result[9]
        
        logger.info(f"Executing saved report: {report_name} (ID: {report_id})")
        
        # Load JSON metadata to get correct table name
        from utils.json_store import load_metadata
        doc_metadata = load_metadata(doc_id)
        if doc_metadata and "duckdb_table_name" in doc_metadata:
            correct_table_name = doc_metadata["duckdb_table_name"]
            # Fix the SQL query to use the correct table name
            import re
            # Find the table name in the SQL (after FROM keyword)
            sql_query = re.sub(r'FROM\s+\w+', f'FROM {correct_table_name}', sql_query, flags=re.IGNORECASE)
            logger.info(f"Corrected SQL to use table: {correct_table_name}")
        else:
            logger.warning(f"Could not load metadata for doc_id: {doc_id}")
        
        # Execute the SQL query via DuckDB
        try:
            # Execute the query
            result = conn.execute(sql_query).fetchall()
            columns = [desc[0] for desc in conn.description] if conn.description else []
            
            # Convert result to list of lists for JSON serialization
            rows = [list(row) for row in result]
            
            # Generate report output using existing report generation logic
            # For now, return a simple summary - can be enhanced later
            report_output = {
                "summary": f"Report '{report_name}' executed successfully with {len(rows)} rows",
                "format": format_type,
                "output_type": output_type,
                "chart": chart,
                "description": description
            }
            
            # Update usage statistics directly
            conn.execute("""
                UPDATE saved_reports 
                SET generation_count = COALESCE(generation_count, 0) + 1,
                    last_generated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, [report_id])
            
            conn.close()
            
            # Return results in same format as /report endpoint
            return {
                "success": True,
                "message": f"Successfully executed report: {report_name}",
                "report_id": report_id,
                "report_name": report_name,
                "sql": sql_query,
                "rows": rows,
                "columns": columns,
                "filters": filters,
                "group_by": group_by,
                "format": format_type,
                "chart": chart,
                "output_type": output_type,
                "description": description,
                "report_output": report_output,
                "execution_time": datetime.now().isoformat(),
                "doc_id": doc_id,
                "row_count": len(rows)
            }
            
        except Exception as sql_error:
            conn.close()
            logger.error(f"SQL execution error for report {report_name}: {sql_error}")
            raise HTTPException(status_code=500, detail=f"Report execution failed: {str(sql_error)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in execute_report endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Report execution failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
