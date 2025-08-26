from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
from dotenv import load_dotenv

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
    """File upload endpoint with validation"""
    # Validate file count
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed")
    
    file_info = []
    for file in files:
        # Validate file size (50MB limit)
        if file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File {file.filename} exceeds 50MB limit")
        
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not an Excel file")
        
        file_info.append({
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type
        })
    
    return {"message": f"Received {len(files)} files", "files": file_info}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
