from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Import Phase 1 modules
from excel_processor import extract_file_metadata, validate_excel_files
from sqlite_manager import create_memory_database

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
        
        # Return files array that frontend expects for AgentChat
        files_data = []
        for i, file in enumerate(validation["valid_files"]):
            file_metadata = metadata.get(file.filename, {})
            files_data.append({
                "name": file.filename,  # Frontend expects 'name' property
                "size": file.size,
                "content_type": file.content_type,
                "fields": file_metadata.get("fields", []),
                "sheets": file_metadata.get("sheets", []),
                "file_index": i
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

@app.post("/analyze-file")
async def analyze_file(request: Dict[str, Any]):
    """
    Handle file-by-file agent analysis
    
    Args:
        request: Dict containing file_info, user_input, and conversation_history
        
    Returns:
        Dict with agent response and completion status
    """
    try:
        # Extract request data
        file_info = request.get("file_info", {})
        user_input = request.get("user_input", "")
        conversation_history = request.get("conversation_history", [])
        
        # Validate required fields
        if not file_info or not user_input:
            raise HTTPException(status_code=400, detail="Missing required fields: file_info and user_input")
        
        # Call AutoGen agent for analysis
        analysis_result = await analyze_single_file(file_info, user_input)
        
        if not analysis_result["success"]:
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        # Determine if file analysis is complete
        # This is a simple heuristic - in practice, the agent would signal completion
        file_complete = bool(analysis_result.get("analysis", {}).get("fields"))
        
        return {
            "success": True,
            "response": analysis_result["analysis"].get("raw_response", "Analysis completed"),
            "analysis": analysis_result["analysis"],
            "file_complete": file_complete,
            "message": "File analysis completed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in file analysis: {e}")
        raise HTTPException(status_code=500, detail=f"File analysis failed: {str(e)}")

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
