"""
JSON Storage Utility for AutoGen Excel Intelligence System

This module handles loading and saving document metadata to .json files.
All operations use explicit doc_id paths as specified in the requirements.

Key Functions:
- save_metadata(doc_id, metadata) - Save document metadata
- load_metadata(doc_id) - Load document metadata  
- append_query_to_metadata(doc_id, query_data) - Add query to document metadata
- append_report_to_metadata(doc_id, report_data) - Add report to document metadata
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

# Configure logging for JSON operations
logger = logging.getLogger(__name__)

def save_metadata(doc_id: str, metadata: Dict[str, Any]) -> bool:
    """
    Save document metadata to .json file using doc_id
    
    Creates or updates a JSON file for the specified document ID.
    The file is stored in the stored_queries directory with the format:
    {doc_id}.json
    
    Args:
        doc_id (str): Document identifier (e.g., "hospital_ledger_fy2024_001")
        metadata (Dict[str, Any]): Document metadata to save
        
    Returns:
        bool: True if save successful, False otherwise
        
    Example:
        success = save_metadata(
            "hospital_ledger_fy2024_001",
            {
                "filename": "hospital_ledger.xlsx",
                "fields": ["Vendor", "Date", "Amount"],
                "record_count": 1220
            }
        )
    """
    try:
        # Ensure stored_queries directory exists
        os.makedirs("stored_queries", exist_ok=True)
        
        # Create file path using doc_id
        json_path = f"stored_queries/{doc_id}.json"
        
        # Add timestamp to metadata
        metadata["last_updated"] = datetime.now().isoformat()
        
        # Save metadata to JSON file
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Successfully saved metadata for doc_id: {doc_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save metadata for doc_id {doc_id}: {str(e)}")
        return False

def load_metadata(doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Load document metadata from .json file using doc_id
    
    Loads metadata from the JSON file associated with the document ID.
    Returns None if file doesn't exist or can't be loaded.
    
    Args:
        doc_id (str): Document identifier
        
    Returns:
        Optional[Dict[str, Any]]: Document metadata or None if not found
        
    Example:
        metadata = load_metadata("hospital_ledger_fy2024_001")
        if metadata:
            print(f"Loaded {metadata['record_count']} records")
    """
    try:
        # Create file path using doc_id
        json_path = f"stored_queries/{doc_id}.json"
        
        # Check if file exists
        if not os.path.exists(json_path):
            logger.warning(f"Metadata file not found for doc_id: {doc_id}")
            return None
        
        # Load metadata from JSON file
        with open(json_path, 'r') as f:
            metadata = json.load(f)
        
        logger.info(f"Successfully loaded metadata for doc_id: {doc_id}")
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to load metadata for doc_id {doc_id}: {str(e)}")
        return None

def append_query_to_metadata(doc_id: str, query_data: Dict[str, Any]) -> bool:
    """
    Append query information to document metadata
    
    Adds query data to the document's metadata file, maintaining a history
    of all queries performed on the document.
    
    Args:
        doc_id (str): Document identifier
        query_data (Dict[str, Any]): Query information to append
        
    Returns:
        bool: True if append successful, False otherwise
        
    Example:
        success = append_query_to_metadata(
            "hospital_ledger_fy2024_001",
            {
                "query_name": "Quarterly Vendor Spend",
                "sql": "SELECT SUM(Amount) FROM hospital_ledger_fy2024_001 WHERE Quarter = 'Q2'",
                "timestamp": "2025-01-15T10:30:00"
            }
        )
    """
    try:
        # Load existing metadata
        metadata = load_metadata(doc_id)
        if not metadata:
            logger.error(f"Cannot append query - metadata not found for doc_id: {doc_id}")
            return False
        
        # Initialize queries list if it doesn't exist
        if "queries" not in metadata:
            metadata["queries"] = []
        
        # Add timestamp to query data
        query_data["timestamp"] = datetime.now().isoformat()
        
        # Append query to list
        metadata["queries"].append(query_data)
        
        # Save updated metadata
        return save_metadata(doc_id, metadata)
        
    except Exception as e:
        logger.error(f"Failed to append query to metadata for doc_id {doc_id}: {str(e)}")
        return False

def append_report_to_metadata(doc_id: str, report_data: Dict[str, Any]) -> bool:
    """
    Append report information to document metadata
    
    Adds report data to the document's metadata file, maintaining a history
    of all reports generated from the document.
    
    Args:
        doc_id (str): Document identifier
        report_data (Dict[str, Any]): Report information to append
        
    Returns:
        bool: True if append successful, False otherwise
        
    Example:
        success = append_report_to_metadata(
            "hospital_ledger_fy2024_001",
            {
                "report_name": "Weekly Vendor Spend",
                "filters": {"vendor": "Vendor X"},
                "output_type": "html",
                "timestamp": "2025-01-15T10:30:00"
            }
        )
    """
    try:
        # Load existing metadata
        metadata = load_metadata(doc_id)
        if not metadata:
            logger.error(f"Cannot append report - metadata not found for doc_id: {doc_id}")
            return False
        
        # Initialize reports list if it doesn't exist
        if "reports" not in metadata:
            metadata["reports"] = []
        
        # Add timestamp to report data
        report_data["timestamp"] = datetime.now().isoformat()
        
        # Append report to list
        metadata["reports"].append(report_data)
        
        # Save updated metadata
        return save_metadata(doc_id, metadata)
        
    except Exception as e:
        logger.error(f"Failed to append report to metadata for doc_id {doc_id}: {str(e)}")
        return False

def get_doc_id_from_filename(filename: str) -> str:
    """
    Generate doc_id from filename following the naming convention
    
    Converts Excel filename to doc_id format as specified in the requirements.
    Format: {base_filename}_{timestamp} (without extension)
    
    Args:
        filename (str): Excel filename (e.g., "hospital_ledger_fy2024.xlsx")
        
    Returns:
        str: Generated doc_id (e.g., "hospital_ledger_fy2024_001")
        
    Example:
        doc_id = get_doc_id_from_filename("hospital_ledger_fy2024.xlsx")
        # Returns: "hospital_ledger_fy2024_001"
    """
    try:
        # Remove file extension
        base_name = os.path.splitext(filename)[0]
        
        # Clean filename (remove spaces, special chars)
        import re
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', base_name)
        
        # Add timestamp suffix for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_id = f"{clean_name}_{timestamp}"
        
        return doc_id
        
    except Exception as e:
        logger.error(f"Failed to generate doc_id from filename {filename}: {str(e)}")
        # Fallback: use filename with timestamp
        return f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def list_available_doc_ids() -> list:
    """
    List all available document IDs from JSON files
    
    Scans the stored_queries directory for JSON files and returns
    their corresponding doc_ids.
    
    Returns:
        list: List of available doc_ids
        
    Example:
        doc_ids = list_available_doc_ids()
        print(f"Found {len(doc_ids)} documents")
    """
    try:
        doc_ids = []
        
        # Check if stored_queries directory exists
        if not os.path.exists("stored_queries"):
            return doc_ids
        
        # Scan for JSON files
        for filename in os.listdir("stored_queries"):
            if filename.endswith('.json'):
                # Remove .json extension to get doc_id
                doc_id = filename[:-5]  # Remove '.json'
                doc_ids.append(doc_id)
        
        # Sort by creation time (newest first)
        doc_ids.sort(key=lambda x: os.path.getctime(f"stored_queries/{x}.json"), reverse=True)
        
        logger.info(f"Found {len(doc_ids)} available doc_ids")
        return doc_ids
        
    except Exception as e:
        logger.error(f"Failed to list available doc_ids: {str(e)}")
        return []
