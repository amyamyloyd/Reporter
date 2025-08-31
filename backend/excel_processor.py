"""
Excel file processing and metadata extraction for Phase 1
ONLY handle Excel file parsing and metadata extraction
DO NOT add business logic, agents, or complex processing
"""
import pandas as pd
import re
from typing import Dict, List, Any
from fastapi import UploadFile


def _normalize_column_name(name: str) -> str:
    """
    Normalize column names for DuckDB compatibility
    
    Excel column names can contain spaces, special characters, and
    other elements that cause SQL issues. This function creates
    safe column names while maintaining readability.
    
    Args:
        name (str): Original column name from Excel
        
    Returns:
        str: Normalized column name safe for SQL
        
    Example:
        safe_name = _normalize_column_name("Company Code")  # Returns: "Company_Code"
        safe_name = _normalize_column_name("Cost ($)")     # Returns: "Cost___"
    """
    # Replace spaces and special chars with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    
    # Ensure starts with letter or underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = 'col_' + sanitized
        
    # Handle empty names
    if not sanitized:
        sanitized = 'unnamed_column'
        
    # Limit length and remove double underscores
    sanitized = re.sub(r'_+', '_', sanitized)[:64]
    
    return sanitized.strip('_')


def extract_file_metadata_from_saved_file(file_path: str) -> Dict[str, Any]:
    """
    Extract basic sheet names, field names, and types from a saved Excel file
    
    Column names are normalized for DuckDB compatibility during extraction.
    This version works with saved file paths instead of file objects.
    
    Args:
        file_path: Path to the saved Excel file
        
    Returns:
        Dict with structure: {"sheets": {"sheet_name": {"fields": [], "normalized_fields": [], "types": {}}}}
    """
    try:
        # Read Excel file with pandas from file path
        df_dict = pd.read_excel(file_path, sheet_name=None)
        
        file_metadata = {"sheets": {}}
        
        for sheet_name, df in df_dict.items():
            # Extract original field names
            original_fields = list(df.columns)
            
            # Normalize field names for DuckDB compatibility
            normalized_fields = [_normalize_column_name(col) for col in original_fields]
            
            # Create field mapping for reference
            field_mapping = dict(zip(original_fields, normalized_fields))
            
            # Extract types from normalized DataFrame
            df_normalized = df.copy()
            df_normalized.columns = normalized_fields
            types = {col: str(df_normalized[col].dtype) for col in normalized_fields}
            
            file_metadata["sheets"][sheet_name] = {
                "fields": original_fields,  # Keep original for display
                "normalized_fields": normalized_fields,  # Clean names for DuckDB
                "field_mapping": field_mapping,  # Original -> Normalized mapping
                "types": types,
                "row_count": len(df)
            }
        
        return file_metadata
        
    except Exception as e:
        # Log error and return error state
        print(f"Error processing {file_path}: {e}")
        return {"error": str(e)}


def extract_file_metadata(uploaded_files: List[UploadFile]) -> Dict[str, Any]:
    """
    Extract basic sheet names, field names, and types from Excel files
    
    Column names are normalized for DuckDB compatibility during extraction.
    
    Args:
        uploaded_files: List of uploaded Excel files
        
    Returns:
        Dict with structure: {"filename": {"sheets": {"sheet_name": {"fields": [], "normalized_fields": [], "types": {}}}}}
    """
    metadata = {}
    
    for file in uploaded_files:
        try:
            # Read Excel file with pandas
            df_dict = pd.read_excel(file.file, sheet_name=None)
            
            file_metadata = {"sheets": {}}
            
            for sheet_name, df in df_dict.items():
                # Extract original field names
                original_fields = list(df.columns)
                
                # Normalize field names for DuckDB compatibility
                normalized_fields = [_normalize_column_name(col) for col in original_fields]
                
                # Create field mapping for reference
                field_mapping = dict(zip(original_fields, normalized_fields))
                
                # Extract types from normalized DataFrame
                df_normalized = df.copy()
                df_normalized.columns = normalized_fields
                types = {col: str(df_normalized[col].dtype) for col in normalized_fields}
                
                file_metadata["sheets"][sheet_name] = {
                    "fields": original_fields,  # Keep original for display
                    "normalized_fields": normalized_fields,  # Clean names for DuckDB
                    "field_mapping": field_mapping,  # Original -> Normalized mapping
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
