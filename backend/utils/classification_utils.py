"""
Classification Utilities - Document Type Management
AutoGen Excel Intelligence System - Classification Enhancement

This module provides backend utilities for document type management including
renaming, reclassification, and retrieval operations.

Purpose: Backend utilities for document type management
- Update document types in both database and JSON metadata
- Rename saved queries and reports
- List available document types
- Provide AI-powered document type suggestions

Type: Utility Module
Dependencies: duckdb, json, typing, logging, os
"""

import duckdb
import json
import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class ClassificationUtils:
    """
    Utility class for document type management operations
    
    This class provides methods for managing document types, queries, and reports
    across both the DuckDB database and JSON metadata files.
    """
    
    def __init__(self, db_path: str = "excel_reporting.db"):
        """
        Initialize classification utilities with database path
        
        Args:
            db_path (str): Path to the DuckDB database file
        """
        self.db_path = db_path
        self.stored_queries_dir = "stored_queries"
        
    def update_document_type(self, doc_id: str, new_type: str, new_type_code: str = None) -> Dict[str, Any]:
        """
        Update document type for a specific document
        
        Args:
            doc_id (str): Document identifier
            new_type (str): New document type name
            new_type_code (str): New document type code (optional)
            
        Returns:
            Dict[str, Any]: Result of the update operation
        """
        try:
            # Generate type code if not provided
            if not new_type_code:
                new_type_code = self._generate_type_code(new_type)
            
            # Update in database
            db_result = self._update_document_type_in_db(doc_id, new_type, new_type_code)
            
            # Update in JSON metadata
            json_result = self._update_document_type_in_json(doc_id, new_type, new_type_code)
            
            return {
                "success": db_result["success"] and json_result["success"],
                "doc_id": doc_id,
                "new_type": new_type,
                "new_type_code": new_type_code,
                "database_updated": db_result["success"],
                "json_updated": json_result["success"],
                "message": f"Document type updated to '{new_type}' ({new_type_code})"
            }
            
        except Exception as e:
            logger.error(f"Error updating document type for {doc_id}: {e}")
            return {
                "success": False,
                "doc_id": doc_id,
                "error": str(e),
                "message": f"Failed to update document type: {e}"
            }
    
    def rename_saved_query(self, query_id: str, new_name: str) -> Dict[str, Any]:
        """
        Rename a saved query
        
        Args:
            query_id (str): Query identifier
            new_name (str): New query name
            
        Returns:
            Dict[str, Any]: Result of the rename operation
        """
        try:
            # Update in database
            db_result = self._rename_query_in_db(query_id, new_name)
            
            # Update in JSON metadata
            json_result = self._rename_query_in_json(query_id, new_name)
            
            return {
                "success": db_result["success"] and json_result["success"],
                "query_id": query_id,
                "new_name": new_name,
                "database_updated": db_result["success"],
                "json_updated": json_result["success"],
                "message": f"Query renamed to '{new_name}'"
            }
            
        except Exception as e:
            logger.error(f"Error renaming query {query_id}: {e}")
            return {
                "success": False,
                "query_id": query_id,
                "error": str(e),
                "message": f"Failed to rename query: {e}"
            }
    
    def rename_saved_report(self, report_id: str, new_name: str) -> Dict[str, Any]:
        """
        Rename a saved report
        
        Args:
            report_id (str): Report identifier
            new_name (str): New report name
            
        Returns:
            Dict[str, Any]: Result of the rename operation
        """
        try:
            # Update in database
            db_result = self._rename_report_in_db(report_id, new_name)
            
            # Update in JSON metadata
            json_result = self._rename_report_in_json(report_id, new_name)
            
            return {
                "success": db_result["success"] and json_result["success"],
                "report_id": report_id,
                "new_name": new_name,
                "database_updated": db_result["success"],
                "json_updated": json_result["success"],
                "message": f"Report renamed to '{new_name}'"
            }
            
        except Exception as e:
            logger.error(f"Error renaming report {report_id}: {e}")
            return {
                "success": False,
                "report_id": report_id,
                "error": str(e),
                "message": f"Failed to rename report: {e}"
            }
    
    def get_known_doc_types(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get list of known document types
        
        Args:
            user_id (str): User identifier (optional, for future multi-user support)
            
        Returns:
            Dict[str, Any]: List of known document types
        """
        try:
            conn = duckdb.connect(self.db_path)
            
            # Get document types from registry
            result = conn.execute("""
                SELECT document_type, document_type_code, description, 
                       reuse_regularly, COUNT(*) as usage_count
                FROM doc_registry
                GROUP BY document_type, document_type_code, description, reuse_regularly
                ORDER BY usage_count DESC, document_type
            """)
            
            doc_types = []
            for row in result.fetchall():
                doc_types.append({
                    "document_type": row[0],
                    "document_type_code": row[1],
                    "description": row[2],
                    "reuse_regularly": row[3],
                    "usage_count": row[4]
                })
            
            conn.close()
            
            return {
                "success": True,
                "doc_types": doc_types,
                "count": len(doc_types),
                "message": f"Found {len(doc_types)} document types"
            }
            
        except Exception as e:
            logger.error(f"Error getting known document types: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get document types: {e}"
            }
    
    def suggest_document_type(self, fields: List[str], existing_types: List[str] = None) -> Dict[str, Any]:
        """
        Suggest document type based on fields using AI-powered analysis
        
        Args:
            fields (List[str]): List of field names from the document
            existing_types (List[str]): List of existing document types to consider
            
        Returns:
            Dict[str, Any]: AI-powered document type suggestions
        """
        try:
            # Import fuzzy matcher for suggestions
            from .fuzzy_classification import create_fuzzy_matcher
            
            # Create fuzzy matcher
            matcher = create_fuzzy_matcher(similarity_threshold=0.7)
            
            # Get suggestions from database
            conn = duckdb.connect(self.db_path)
            suggestions = matcher.find_similar_document_types(fields, conn, limit=5)
            conn.close()
            
            # Format suggestions
            formatted_suggestions = []
            for suggestion in suggestions:
                formatted_suggestions.append({
                    "document_type": suggestion.document_type,
                    "document_type_code": suggestion.document_type_code,
                    "similarity_score": suggestion.similarity_score,
                    "confidence_level": suggestion.confidence_level,
                    "matching_fields": suggestion.matching_fields,
                    "description": suggestion.description
                })
            
            # Generate AI-powered suggestions if no good matches
            ai_suggestions = []
            if not formatted_suggestions or formatted_suggestions[0]["similarity_score"] < 0.8:
                ai_suggestions = self._generate_ai_suggestions(fields)
            
            return {
                "success": True,
                "suggestions": formatted_suggestions,
                "ai_suggestions": ai_suggestions,
                "field_count": len(fields),
                "message": f"Generated {len(formatted_suggestions)} database suggestions and {len(ai_suggestions)} AI suggestions"
            }
            
        except Exception as e:
            logger.error(f"Error suggesting document type: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to suggest document type: {e}"
            }
    
    def _update_document_type_in_db(self, doc_id: str, new_type: str, new_type_code: str) -> Dict[str, Any]:
        """Update document type in database"""
        try:
            conn = duckdb.connect(self.db_path)
            
            # Update doc_registry table
            result = conn.execute("""
                UPDATE doc_registry 
                SET document_type = ?, document_type_code = ?
                WHERE id = (SELECT id FROM doc_registry WHERE field_pattern LIKE ? LIMIT 1)
            """, [new_type, new_type_code, f"%{doc_id}%"])
            
            conn.close()
            
            return {"success": True, "rows_affected": result.rowcount}
            
        except Exception as e:
            logger.error(f"Error updating document type in database: {e}")
            return {"success": False, "error": str(e)}
    
    def _update_document_type_in_json(self, doc_id: str, new_type: str, new_type_code: str) -> Dict[str, Any]:
        """Update document type in JSON metadata"""
        try:
            json_file = os.path.join(self.stored_queries_dir, f"{doc_id}.json")
            
            if not os.path.exists(json_file):
                return {"success": False, "error": "JSON file not found"}
            
            # Load existing metadata
            with open(json_file, 'r') as f:
                metadata = json.load(f)
            
            # Update document type
            metadata["document_type"] = new_type
            metadata["document_type_code"] = new_type_code
            metadata["last_updated"] = datetime.now().isoformat()
            
            # Save updated metadata
            with open(json_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error updating document type in JSON: {e}")
            return {"success": False, "error": str(e)}
    
    def _rename_query_in_db(self, query_id: str, new_name: str) -> Dict[str, Any]:
        """Rename query in database"""
        try:
            conn = duckdb.connect(self.db_path)
            
            result = conn.execute("""
                UPDATE saved_queries 
                SET query_name = ?
                WHERE query_name = ?
            """, [new_name, query_id])
            
            conn.close()
            
            return {"success": True, "rows_affected": result.rowcount}
            
        except Exception as e:
            logger.error(f"Error renaming query in database: {e}")
            return {"success": False, "error": str(e)}
    
    def _rename_query_in_json(self, query_id: str, new_name: str) -> Dict[str, Any]:
        """Rename query in JSON metadata"""
        try:
            # Find JSON files containing the query
            json_files = [f for f in os.listdir(self.stored_queries_dir) if f.endswith('.json')]
            
            updated_files = 0
            for json_file in json_files:
                file_path = os.path.join(self.stored_queries_dir, json_file)
                
                with open(file_path, 'r') as f:
                    metadata = json.load(f)
                
                # Update query name in saved_queries if it exists
                if "saved_queries" in metadata:
                    for query in metadata["saved_queries"]:
                        if query.get("query_name") == query_id:
                            query["query_name"] = new_name
                            query["last_updated"] = datetime.now().isoformat()
                            updated_files += 1
                
                # Save updated metadata
                with open(file_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            return {"success": True, "files_updated": updated_files}
            
        except Exception as e:
            logger.error(f"Error renaming query in JSON: {e}")
            return {"success": False, "error": str(e)}
    
    def _rename_report_in_db(self, report_id: str, new_name: str) -> Dict[str, Any]:
        """Rename report in database"""
        try:
            conn = duckdb.connect(self.db_path)
            
            result = conn.execute("""
                UPDATE saved_reports 
                SET report_name = ?
                WHERE report_name = ?
            """, [new_name, report_id])
            
            conn.close()
            
            return {"success": True, "rows_affected": result.rowcount}
            
        except Exception as e:
            logger.error(f"Error renaming report in database: {e}")
            return {"success": False, "error": str(e)}
    
    def _rename_report_in_json(self, report_id: str, new_name: str) -> Dict[str, Any]:
        """Rename report in JSON metadata"""
        try:
            # Find JSON files containing the report
            json_files = [f for f in os.listdir(self.stored_queries_dir) if f.endswith('.json')]
            
            updated_files = 0
            for json_file in json_files:
                file_path = os.path.join(self.stored_queries_dir, json_file)
                
                with open(file_path, 'r') as f:
                    metadata = json.load(f)
                
                # Update report name in saved_reports if it exists
                if "saved_reports" in metadata:
                    for report in metadata["saved_reports"]:
                        if report.get("report_name") == report_id:
                            report["report_name"] = new_name
                            report["last_updated"] = datetime.now().isoformat()
                            updated_files += 1
                
                # Save updated metadata
                with open(file_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            return {"success": True, "files_updated": updated_files}
            
        except Exception as e:
            logger.error(f"Error renaming report in JSON: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_type_code(self, document_type: str) -> str:
        """Generate a type code from document type name"""
        # Remove common words and create acronym
        words = document_type.replace("_", " ").replace("-", " ").split()
        filtered_words = [word for word in words if word.lower() not in ["the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for", "with", "by"]]
        
        if not filtered_words:
            return document_type[:5].upper()
        
        # Create acronym from first letters
        code = "".join([word[0].upper() for word in filtered_words[:5]])
        return code
    
    def _generate_ai_suggestions(self, fields: List[str]) -> List[Dict[str, Any]]:
        """Generate AI-powered document type suggestions"""
        try:
            # Handle None or empty fields
            if not fields:
                return [{
                    "document_type": "Data Document",
                    "document_type_code": "DATA",
                    "confidence": "low",
                    "reasoning": "No fields provided for analysis"
                }]
            
            # Simple AI-powered suggestions based on field analysis
            suggestions = []
            
            # Analyze fields for common patterns
            field_analysis = self._analyze_fields(fields)
            
            # Generate suggestions based on analysis
            if field_analysis["has_financial"]:
                suggestions.append({
                    "document_type": "Financial Report",
                    "document_type_code": "FIN",
                    "confidence": "high",
                    "reasoning": "Contains financial fields like amount, cost, revenue"
                })
            
            if field_analysis["has_temporal"]:
                suggestions.append({
                    "document_type": "Time-based Data",
                    "document_type_code": "TIME",
                    "confidence": "medium",
                    "reasoning": "Contains date/time fields"
                })
            
            if field_analysis["has_identification"]:
                suggestions.append({
                    "document_type": "Reference Data",
                    "document_type_code": "REF",
                    "confidence": "medium",
                    "reasoning": "Contains ID/reference fields"
                })
            
            # Generic suggestion if no specific patterns
            if not suggestions:
                suggestions.append({
                    "document_type": "Data Document",
                    "document_type_code": "DATA",
                    "confidence": "low",
                    "reasoning": "General data document based on field count"
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating AI suggestions: {e}")
            return []
    
    def _analyze_fields(self, fields: List[str]) -> Dict[str, Any]:
        """Analyze fields for common patterns"""
        analysis = {
            "has_financial": False,
            "has_temporal": False,
            "has_identification": False,
            "has_location": False,
            "has_person": False
        }
        
        financial_keywords = ["amount", "cost", "price", "revenue", "expense", "budget", "total", "sum"]
        temporal_keywords = ["date", "time", "timestamp", "created", "updated", "when"]
        id_keywords = ["id", "number", "code", "key", "reference", "ref"]
        location_keywords = ["location", "address", "city", "state", "country", "region"]
        person_keywords = ["name", "person", "user", "employee", "staff", "contact"]
        
        for field in fields:
            field_lower = field.lower()
            
            if any(keyword in field_lower for keyword in financial_keywords):
                analysis["has_financial"] = True
            if any(keyword in field_lower for keyword in temporal_keywords):
                analysis["has_temporal"] = True
            if any(keyword in field_lower for keyword in id_keywords):
                analysis["has_identification"] = True
            if any(keyword in field_lower for keyword in location_keywords):
                analysis["has_location"] = True
            if any(keyword in field_lower for keyword in person_keywords):
                analysis["has_person"] = True
        
        return analysis

# Convenience functions for easy usage
def create_classification_utils(db_path: str = "excel_reporting.db") -> ClassificationUtils:
    """
    Create a new ClassificationUtils instance
    
    Args:
        db_path (str): Path to the DuckDB database file
        
    Returns:
        ClassificationUtils: Configured classification utilities
    """
    return ClassificationUtils(db_path)

def update_document_type(doc_id: str, new_type: str, new_type_code: str = None) -> Dict[str, Any]:
    """
    Update document type for a specific document
    
    Args:
        doc_id (str): Document identifier
        new_type (str): New document type name
        new_type_code (str): New document type code (optional)
        
    Returns:
        Dict[str, Any]: Result of the update operation
    """
    utils = create_classification_utils()
    return utils.update_document_type(doc_id, new_type, new_type_code)

def rename_saved_query(query_id: str, new_name: str) -> Dict[str, Any]:
    """
    Rename a saved query
    
    Args:
        query_id (str): Query identifier
        new_name (str): New query name
        
    Returns:
        Dict[str, Any]: Result of the rename operation
    """
    utils = create_classification_utils()
    return utils.rename_saved_query(query_id, new_name)

def rename_saved_report(report_id: str, new_name: str) -> Dict[str, Any]:
    """
    Rename a saved report
    
    Args:
        report_id (str): Report identifier
        new_name (str): New report name
        
    Returns:
        Dict[str, Any]: Result of the rename operation
    """
    utils = create_classification_utils()
    return utils.rename_saved_report(report_id, new_name)

def get_known_doc_types(user_id: str = None) -> Dict[str, Any]:
    """
    Get list of known document types
    
    Args:
        user_id (str): User identifier (optional)
        
    Returns:
        Dict[str, Any]: List of known document types
    """
    utils = create_classification_utils()
    return utils.get_known_doc_types(user_id)

def suggest_document_type(fields: List[str], existing_types: List[str] = None) -> Dict[str, Any]:
    """
    Suggest document type based on fields
    
    Args:
        fields (List[str]): List of field names
        existing_types (List[str]): List of existing document types (optional)
        
    Returns:
        Dict[str, Any]: Document type suggestions
    """
    utils = create_classification_utils()
    return utils.suggest_document_type(fields, existing_types)

# Example usage and testing
if __name__ == "__main__":
    # Test the classification utilities
    try:
        print("=== Classification Utilities Test ===")
        
        # Create utilities instance
        utils = create_classification_utils()
        
        # Test field analysis
        test_fields = ["Invoice_Number", "Date", "Amount", "Customer_Name"]
        analysis = utils._analyze_fields(test_fields)
        print(f"Field analysis for {test_fields}: {analysis}")
        
        # Test type code generation
        type_code = utils._generate_type_code("Hospital Finance Document")
        print(f"Type code for 'Hospital Finance Document': {type_code}")
        
        # Test AI suggestions
        suggestions = utils._generate_ai_suggestions(test_fields)
        print(f"AI suggestions for {test_fields}: {suggestions}")
        
        print("\n✅ Classification utilities test completed successfully")
        
    except Exception as e:
        print(f"❌ Classification utilities test failed: {e}")
        import traceback
        traceback.print_exc()
