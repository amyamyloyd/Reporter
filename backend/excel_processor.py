"""
Excel file processing and metadata extraction for Phase 1
ONLY handle Excel file parsing and metadata extraction
DO NOT add business logic, agents, or complex processing
"""
import pandas as pd
from typing import Dict, List, Any
from fastapi import UploadFile


def extract_file_metadata(uploaded_files: List[UploadFile]) -> Dict[str, Any]:
    """
    Extract basic sheet names, field names, and types from Excel files
    
    Args:
        uploaded_files: List of uploaded Excel files
        
    Returns:
        Dict with structure: {"filename": {"sheets": {"sheet_name": {"fields": [], "types": {}}}}}
    """
    metadata = {}
    
    for file in uploaded_files:
        try:
            # Read Excel file with pandas
            df_dict = pd.read_excel(file.file, sheet_name=None)
            
            file_metadata = {"sheets": {}}
            
            for sheet_name, df in df_dict.items():
                # Extract field names and types
                fields = list(df.columns)
                types = {col: str(df[col].dtype) for col in fields}
                
                file_metadata["sheets"][sheet_name] = {
                    "fields": fields,
                    "types": types,
                    "row_count": len(df)
                }
            
            metadata[file.filename] = file_metadata
            
        except Exception as e:
            # Log error and continue with other files
            print(f"Error processing {file.filename}: {e}")
            metadata[file.filename] = {"error": str(e)}
    
    return metadata


def validate_excel_files(files: List[UploadFile]) -> Dict[str, Any]:
    """
    Check file size (<50MB), type (.xlsx/.xls), count (<=5)
    
    Args:
        files: List of uploaded files
        
    Returns:
        Dict with validation results
    """
    validation_results = {
        "valid_files": [],
        "rejected_files": [],
        "errors": []
    }
    
    # Check file count
    if len(files) > 5:
        validation_results["errors"].append("Maximum 5 files allowed")
        return validation_results
    
    for file in files:
        file_errors = []
        
        # Check file size (50MB limit)
        if file.size > 50 * 1024 * 1024:
            file_errors.append(f"File size {file.size / (1024*1024):.1f}MB exceeds 50MB limit")
        
        # Check file type
        if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            file_errors.append("File must be .xlsx or .xls format")
        
        # Check content type - be more permissive for testing
        # Excel files uploaded via curl often have generic content types
        if file.content_type and file.content_type != "application/octet-stream":
            if not (file.content_type.startswith('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') or \
                   file.content_type.startswith('application/vnd.ms-excel')):
                file_errors.append("Invalid Excel file content type")
        
        if file_errors:
            validation_results["rejected_files"].append({
                "filename": file.filename,
                "errors": file_errors
            })
        else:
            validation_results["valid_files"].append(file)  # Return the actual file object, not just filename
    
    return validation_results
