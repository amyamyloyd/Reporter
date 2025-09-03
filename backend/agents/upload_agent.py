"""
UploadAgent - Metadata Enrichment After File Upload
AutoGen Excel Intelligence System - Phase 3

This agent handles metadata enrichment after file upload.

Type: ConversableAgent
Purpose: Metadata enrichment after file upload
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# Import AutoGen components
try:
    from autogen import ConversableAgent
except ImportError as e:
    logging.error(f"Failed to import AutoGen components: {e}")
    raise

# Import our utility modules
from utils.json_store import save_metadata, load_metadata

# Configure logging
logger = logging.getLogger(__name__)

class UploadAgent(ConversableAgent):
    """
    UploadAgent - Metadata enrichment after file upload
    
    Responsibilities:
    - Called after /upload endpoint succeeds
    - Prompt user: "What is this file?", "Add notes, label, project ID"
    - Update .json metadata for the file (via save_metadata())
    - Update doc_registry for file type → description, usage context
    """
    
    def __init__(self, name: str = "UploadAgent"):
        """
        Initialize UploadAgent with AutoGen configuration
        
        Args:
            name (str): Agent name identifier
        """
        # AutoGen 0.4.0+ configuration - cost-optimized as per rules
        config_list = [{
            "model": "gpt-4",  # Cost-optimized
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "max_tokens": 500,  # Keep responses concise
            "temperature": 0.1,  # More deterministic
            "timeout": 30
        }]
        
        # System message for upload metadata enrichment
        system_message = """You are a metadata enrichment specialist for Excel file uploads.

Your job:
1. Ask user what the file represents
2. Collect notes, labels, project IDs
3. Update .json metadata for the file
4. Update doc_registry for file type classification

Always return JSON with:
- file_purpose: What the file represents
- notes: User notes about the file
- label: User-provided label
- project_id: Associated project ID
- doc_type: Classified document type
- usage_context: How the file will be used

Be conversational and helpful in gathering metadata."""

        try:
            super().__init__(
                name=name,
                llm_config={"config_list": config_list},
                system_message=system_message,
                human_input_mode="NEVER",  # Automated for POC
                max_consecutive_auto_reply=3
            )
            logger.info(f"UploadAgent '{name}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize UploadAgent: {e}")
            raise

    def process_upload_request(self, structured_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process upload metadata enrichment request
        
        Args:
            structured_input (Dict[str, Any]): Structured input containing:
                - doc_id: Document identifier
                - query_text: User's description of the file
                - context: Schema, metadata, etc.
                - datetime_context: Time context
                
        Returns:
            Dict[str, Any]: Metadata enrichment results
        """
        try:
            # Extract input data
            doc_id = structured_input.get("doc_id", "")
            query_text = structured_input.get("query_text", "")
            context = structured_input.get("context", {})
            datetime_context = structured_input.get("datetime_context", {})
            
            logger.info(f"UploadAgent processing metadata enrichment for doc_id: {doc_id}")
            logger.info(f"User description: {query_text[:100]}...")
            
            # Load existing metadata
            existing_metadata = load_metadata(doc_id)
            if not existing_metadata:
                return {
                    "success": False,
                    "error": f"No existing metadata found for doc_id: {doc_id}",
                    "enriched_metadata": {},
                    "summary": "Metadata enrichment failed - no existing metadata"
                }
            
            # Generate enriched metadata using LLM
            enriched_metadata = self._generate_enriched_metadata(query_text, existing_metadata, context)
            
            if not enriched_metadata.get("success", False):
                return enriched_metadata
            
            # Update metadata file
            update_success = self._update_metadata_file(doc_id, enriched_metadata["metadata"])
            
            if not update_success:
                return {
                    "success": False,
                    "error": "Failed to update metadata file",
                    "enriched_metadata": enriched_metadata["metadata"],
                    "summary": "Metadata enrichment completed but file update failed"
                }
            
            # Prepare final result
            enrichment_result = {
                "success": True,
                "doc_id": doc_id,
                "enriched_metadata": enriched_metadata["metadata"],
                "summary": f"Metadata enriched for {doc_id}: {enriched_metadata['metadata'].get('file_purpose', 'Unknown purpose')}",
                "enrichment_time": datetime_context.get("now", "unknown")
            }
            
            logger.info(f"UploadAgent completed successfully for doc_id: {doc_id}")
            return enrichment_result
            
        except Exception as e:
            logger.error(f"Error in UploadAgent processing: {e}")
            return {
                "success": False,
                "error": f"Metadata enrichment failed: {str(e)}",
                "enriched_metadata": {},
                "summary": "Metadata enrichment failed due to processing error"
            }

    def _generate_enriched_metadata(self, user_description: str, existing_metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate enriched metadata using LLM
        
        Args:
            user_description (str): User's description of the file
            existing_metadata (Dict[str, Any]): Existing metadata
            context (Dict[str, Any]): Additional context
            
        Returns:
            Dict[str, Any]: Enriched metadata result
        """
        try:
            # For POC, we'll use a simplified metadata enrichment
            # In production, this would use the agent's LLM
            enriched_metadata = self._simple_metadata_enrichment(user_description, existing_metadata, context)
            
            return {
                "success": True,
                "metadata": enriched_metadata
            }
            
        except Exception as e:
            logger.error(f"Error generating enriched metadata: {e}")
            return {
                "success": False,
                "error": f"Metadata enrichment generation failed: {str(e)}"
            }

    def _simple_metadata_enrichment(self, user_description: str, existing_metadata: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple metadata enrichment for POC (replace with LLM in production)
        
        Args:
            user_description (str): User's description
            existing_metadata (Dict[str, Any]): Existing metadata
            context (Dict[str, Any]): Context information
            
        Returns:
            Dict[str, Any]: Enriched metadata
        """
        # Start with existing metadata
        enriched = existing_metadata.copy()
        
        # Add user description as file purpose
        enriched["file_purpose"] = user_description or "User uploaded file"
        
        # Add enrichment metadata
        enriched["enrichment"] = {
            "enriched_by": "UploadAgent",
            "enrichment_timestamp": "now",
            "user_description": user_description,
            "schema_fields": context.get("schema", []),
            "record_count": context.get("record_count", 0)
        }
        
        # Add notes if provided
        if user_description:
            enriched["notes"] = f"User description: {user_description}"
        
        # Add label based on filename or description
        filename = existing_metadata.get("filename", "")
        if filename:
            enriched["label"] = filename.replace(".xlsx", "").replace("_", " ").title()
        
        # Add project ID if mentioned
        if "project" in user_description.lower():
            enriched["project_id"] = "user_mentioned_project"
        
        # Classify document type
        enriched["doc_type"] = self._classify_document_type(user_description, context.get("schema", []))
        
        # Add usage context
        enriched["usage_context"] = "Data analysis and reporting"
        
        return enriched

    def _classify_document_type(self, user_description: str, schema: list) -> str:
        """
        Classify document type based on description and schema
        
        Args:
            user_description (str): User's description
            schema (list): Available fields
            
        Returns:
            str: Classified document type
        """
        description_lower = user_description.lower()
        schema_lower = [field.lower() for field in schema]
        
        # Simple classification logic
        if any(word in description_lower for word in ["financial", "budget", "cost", "expense", "revenue"]):
            return "Financial"
        elif any(word in description_lower for word in ["employee", "staff", "personnel", "hr"]):
            return "Human Resources"
        elif any(word in description_lower for word in ["inventory", "stock", "product", "item"]):
            return "Inventory"
        elif any(word in description_lower for word in ["project", "task", "assignment"]):
            return "Project Management"
        elif any(word in schema_lower for word in ["vendor", "supplier", "contractor"]):
            return "Vendor Management"
        else:
            return "General Data"

    def _update_metadata_file(self, doc_id: str, enriched_metadata: Dict[str, Any]) -> bool:
        """
        Update metadata file with enriched data
        
        Args:
            doc_id (str): Document identifier
            enriched_metadata (Dict[str, Any]): Enriched metadata
            
        Returns:
            bool: Success status
        """
        try:
            # Save enriched metadata
            success = save_metadata(doc_id, enriched_metadata)
            
            if success:
                logger.info(f"Metadata file updated successfully for doc_id: {doc_id}")
            else:
                logger.warning(f"Failed to update metadata file for doc_id: {doc_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating metadata file: {e}")
            return False

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent for debugging/monitoring
        
        Returns:
            Dict[str, Any]: Agent information
        """
        return {
            "name": self.name,
            "type": "ConversableAgent",
            "purpose": "Metadata enrichment after file upload",
            "capabilities": [
                "File purpose identification",
                "Metadata enrichment",
                "Document type classification",
                "Usage context determination"
            ],
            "llm_config": self.llm_config
        }

def create_upload_agent(name: str = "UploadAgent") -> UploadAgent:
    """
    Factory function to create an UploadAgent instance
    
    Args:
        name (str): Agent name identifier
        
    Returns:
        UploadAgent: Configured UploadAgent instance
    """
    try:
        agent = UploadAgent(name=name)
        logger.info(f"UploadAgent '{name}' created successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to create UploadAgent: {e}")
        raise

# Example usage and testing
if __name__ == "__main__":
    # Test UploadAgent creation and basic functionality
    try:
        # Create agent
        upload_agent = create_upload_agent()
        
        # Test with sample input
        sample_input = {
            "doc_id": "hospital_ledger_fy2024_001",
            "query_text": "This file contains hospital financial data for Q2 2024",
            "context": {
                "schema": ["Vendor", "Date", "Amount"],
                "record_count": 1200,
                "duckdb_table_name": "hospital_ledger_fy2024_001"
            },
            "datetime_context": {"now": "2025-09-02"}
        }
        
        # Process upload request
        upload_result = upload_agent.process_upload_request(sample_input)
        
        print("=== UploadAgent Test Results ===")
        print(f"Agent Info: {upload_agent.get_agent_info()}")
        print(f"Upload Result: {json.dumps(upload_result, indent=2, default=str)}")
        
    except Exception as e:
        print(f"UploadAgent test failed: {e}")
