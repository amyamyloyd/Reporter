"""
MemoryAgent - Fetch Saved Queries/Reports
AutoGen Excel Intelligence System - Phase 3

This agent handles retrieval of saved queries and reports from DuckDB.

Type: ToolAgent
Purpose: Fetch saved queries/reports
"""

import os
import json
import logging
import duckdb
from typing import Dict, Any, Optional, List

# Import AutoGen components
try:
    from autogen import ConversableAgent
except ImportError as e:
    logging.error(f"Failed to import AutoGen components: {e}")
    raise

# Import our utility modules
from utils.duckdb_manager import get_saved_queries, get_saved_reports, get_query_by_name

# Configure logging
logger = logging.getLogger(__name__)

class MemoryAgent(ConversableAgent):
    """
    MemoryAgent - Fetch saved queries and reports from DuckDB
    
    Responsibilities:
    - Accept lookup dict: doc_id, query_name, tags
    - Search DuckDB: saved_queries, saved_reports
    - Return full SQL or report definition
    """
    
    def __init__(self, name: str = "MemoryAgent"):
        """
        Initialize MemoryAgent with AutoGen configuration
        
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
        
        # System message for memory retrieval
        system_message = """You are a memory retrieval specialist for Excel data analysis.

Your job:
1. Search saved queries and reports in DuckDB
2. Return full SQL or report definitions
3. Handle lookup by doc_id, query_name, tags
4. Provide comprehensive memory search results

Always return JSON with:
- search_results: Found queries/reports
- total_count: Number of results found
- search_criteria: What was searched for
- summary: Brief summary of results

Be thorough in searching and precise in returning results."""

        try:
            super().__init__(
                name=name,
                llm_config={"config_list": config_list},
                system_message=system_message,
                human_input_mode="NEVER",  # Automated for POC
                max_consecutive_auto_reply=3
            )
            logger.info(f"MemoryAgent '{name}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MemoryAgent: {e}")
            raise

    def process_memory_request(self, structured_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process memory retrieval request
        
        Args:
            structured_input (Dict[str, Any]): Structured input containing:
                - doc_id: Document identifier
                - query_text: User's memory request
                - context: Additional context
                - datetime_context: Time context
                
        Returns:
            Dict[str, Any]: Memory retrieval results
        """
        try:
            # Extract input data
            doc_id = structured_input.get("doc_id", "")
            query_text = structured_input.get("query_text", "")
            context = structured_input.get("context", {})
            datetime_context = structured_input.get("datetime_context", {})
            
            logger.info(f"MemoryAgent processing memory request for doc_id: {doc_id}")
            logger.info(f"Memory request: {query_text[:100]}...")
            
            # Parse memory request to determine what to search for
            search_criteria = self._parse_memory_request(query_text, doc_id, context)
            
            # Search for saved queries and reports
            search_results = self._search_memory(search_criteria)
            
            # Prepare final result
            memory_result = {
                "success": True,
                "doc_id": doc_id,
                "search_criteria": search_criteria,
                "search_results": search_results,
                "total_count": len(search_results.get("queries", [])) + len(search_results.get("reports", [])),
                "summary": f"Found {len(search_results.get('queries', []))} queries and {len(search_results.get('reports', []))} reports",
                "search_time": datetime_context.get("now", "unknown")
            }
            
            logger.info(f"MemoryAgent completed successfully for doc_id: {doc_id}")
            return memory_result
            
        except Exception as e:
            logger.error(f"Error in MemoryAgent processing: {e}")
            return {
                "success": False,
                "error": f"Memory retrieval failed: {str(e)}",
                "search_results": {"queries": [], "reports": []},
                "total_count": 0,
                "summary": "Memory retrieval failed due to processing error"
            }

    def _parse_memory_request(self, query_text: str, doc_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse memory request to determine search criteria
        
        Args:
            query_text (str): User's memory request
            doc_id (str): Document identifier
            context (Dict[str, Any]): Additional context
            
        Returns:
            Dict[str, Any]: Search criteria
        """
        query_lower = query_text.lower()
        
        # Determine search type
        search_type = "all"  # Default to search both queries and reports
        if "query" in query_lower or "question" in query_lower:
            search_type = "queries"
        elif "report" in query_lower or "summary" in query_lower:
            search_type = "reports"
        
        # Extract specific names or tags
        specific_name = None
        tags = []
        
        # Look for specific query/report names
        if "named" in query_lower or "called" in query_lower:
            # Extract name from query (simplified for POC)
            words = query_text.split()
            for i, word in enumerate(words):
                if word.lower() in ["named", "called"] and i + 1 < len(words):
                    specific_name = words[i + 1].strip('"\'.,!?')
                    break
        
        # Look for tags
        if "tag" in query_lower:
            # Extract tags (simplified for POC)
            if "vendor" in query_lower:
                tags.append("vendor")
            if "financial" in query_lower:
                tags.append("financial")
            if "q2" in query_lower or "quarter" in query_lower:
                tags.append("quarterly")
        
        return {
            "search_type": search_type,
            "doc_id": doc_id,
            "specific_name": specific_name,
            "tags": tags,
            "query_text": query_text
        }

    def _search_memory(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search memory (saved queries and reports) based on criteria
        
        Args:
            search_criteria (Dict[str, Any]): Search criteria
            
        Returns:
            Dict[str, Any]: Search results
        """
        try:
            # Connect to DuckDB
            conn = duckdb.connect("excel_reporting.db")
            
            results = {"queries": [], "reports": []}
            
            # Search queries if requested
            if search_criteria["search_type"] in ["all", "queries"]:
                queries = self._search_saved_queries(conn, search_criteria)
                results["queries"] = queries
            
            # Search reports if requested
            if search_criteria["search_type"] in ["all", "reports"]:
                reports = self._search_saved_reports(conn, search_criteria)
                results["reports"] = reports
            
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching memory: {e}")
            return {"queries": [], "reports": []}

    def _search_saved_queries(self, conn: duckdb.DuckDBPyConnection, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search saved queries based on criteria
        
        Args:
            conn: DuckDB connection
            search_criteria: Search criteria
            
        Returns:
            List[Dict[str, Any]]: Found queries
        """
        try:
            # Build query based on criteria
            if search_criteria["specific_name"]:
                # Search by specific name
                query = "SELECT * FROM saved_queries WHERE query_name = ?"
                params = [search_criteria["specific_name"]]
            elif search_criteria["doc_id"]:
                # Search by doc_id
                query = "SELECT * FROM saved_queries WHERE doc_id = ?"
                params = [search_criteria["doc_id"]]
            else:
                # Search all queries
                query = "SELECT * FROM saved_queries LIMIT 10"
                params = []
            
            # Execute query
            result = conn.execute(query, params).fetchall()
            
            # Convert to list of dicts
            queries = []
            for row in result:
                query_dict = {
                    "query_id": row[0],
                    "doc_id": row[1],
                    "query_name": row[2],
                    "query_text": row[3],
                    "sql": row[4],
                    "tags": row[5],
                    "created_at": row[6],
                    "use_count": row[7],
                    "last_used": row[8]
                }
                queries.append(query_dict)
            
            return queries
            
        except Exception as e:
            logger.error(f"Error searching saved queries: {e}")
            return []

    def _search_saved_reports(self, conn: duckdb.DuckDBPyConnection, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search saved reports based on criteria
        
        Args:
            conn: DuckDB connection
            search_criteria: Search criteria
            
        Returns:
            List[Dict[str, Any]]: Found reports
        """
        try:
            # Build query based on criteria
            if search_criteria["specific_name"]:
                # Search by specific name
                query = "SELECT * FROM saved_reports WHERE report_name = ?"
                params = [search_criteria["specific_name"]]
            elif search_criteria["doc_id"]:
                # Search by doc_id
                query = "SELECT * FROM saved_reports WHERE doc_id = ?"
                params = [search_criteria["doc_id"]]
            else:
                # Search all reports
                query = "SELECT * FROM saved_reports LIMIT 10"
                params = []
            
            # Execute query
            result = conn.execute(query, params).fetchall()
            
            # Convert to list of dicts
            reports = []
            for row in result:
                report_dict = {
                    "report_id": row[0],
                    "doc_id": row[1],
                    "report_name": row[2],
                    "sql": row[3],
                    "filters": row[4],
                    "group_by": row[5],
                    "format": row[6],
                    "chart": row[7],
                    "output_type": row[8],
                    "description": row[9],
                    "created_at": row[10],
                    "generation_count": row[11],
                    "last_generated": row[12]
                }
                reports.append(report_dict)
            
            return reports
            
        except Exception as e:
            logger.error(f"Error searching saved reports: {e}")
            return []

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent for debugging/monitoring
        
        Returns:
            Dict[str, Any]: Agent information
        """
        return {
            "name": self.name,
            "type": "ConversableAgent",
            "purpose": "Fetch saved queries and reports from DuckDB",
            "capabilities": [
                "Saved queries retrieval",
                "Saved reports retrieval",
                "Search by doc_id, name, or tags",
                "Comprehensive memory search"
            ],
            "llm_config": self.llm_config
        }

def create_memory_agent(name: str = "MemoryAgent") -> MemoryAgent:
    """
    Factory function to create a MemoryAgent instance
    
    Args:
        name (str): Agent name identifier
        
    Returns:
        MemoryAgent: Configured MemoryAgent instance
    """
    try:
        agent = MemoryAgent(name=name)
        logger.info(f"MemoryAgent '{name}' created successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to create MemoryAgent: {e}")
        raise

# Example usage and testing
if __name__ == "__main__":
    # Test MemoryAgent creation and basic functionality
    try:
        # Create agent
        memory_agent = create_memory_agent()
        
        # Test with sample input
        sample_input = {
            "doc_id": "hospital_ledger_fy2024_001",
            "query_text": "Show me my saved queries",
            "context": {
                "schema": ["Vendor", "Date", "Amount"],
                "record_count": 1200,
                "duckdb_table_name": "hospital_ledger_fy2024_001"
            },
            "datetime_context": {"now": "2025-09-02"}
        }
        
        # Process memory request
        memory_result = memory_agent.process_memory_request(sample_input)
        
        print("=== MemoryAgent Test Results ===")
        print(f"Agent Info: {memory_agent.get_agent_info()}")
        print(f"Memory Result: {json.dumps(memory_result, indent=2, default=str)}")
        
    except Exception as e:
        print(f"MemoryAgent test failed: {e}")
