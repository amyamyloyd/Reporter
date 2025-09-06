"""
ReportAgent - Interpret and Build Grouped/Filtered Reports
AutoGen Excel Intelligence System - Phase 3

This agent interprets report specifications and builds reports using
the report_builder.py utility.

Type: ConversableAgent
Purpose: Interpret and build grouped/filtered reports
"""

import os
import json
import logging
import duckdb
import time
from typing import Dict, Any, Optional, List

# Import AutoGen components
try:
    from autogen import ConversableAgent
except ImportError as e:
    logging.error(f"Failed to import AutoGen components: {e}")
    raise

# Import our utility modules
from utils.report_builder import build_report
from utils.duckdb_manager import save_report, check_sql_uniqueness
from utils.json_store import load_metadata, append_report_to_metadata

# Configure logging
logger = logging.getLogger(__name__)

class ReportAgent(ConversableAgent):
    """
    ReportAgent - Interpret and build grouped/filtered reports
    
    Responsibilities:
    - Accept report specification
    - Prompt LLM to interpret vague titles and determine logic
    - Use report_builder.py for assembly
    - Save to .json and saved_reports
    - Return HTML, XLSX, or JSON based on output_type
    """
    
    def __init__(self, name: str = "ReportAgent"):
        """
        Initialize ReportAgent with AutoGen configuration
        
        Args:
            name (str): Agent name identifier
        """
        # AutoGen 0.4.0+ configuration - cost-optimized as per rules
        config_list = [{
            "model": "gpt-4",  # Cost-optimized
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "max_tokens": 1000,  # More tokens for report generation
            "temperature": 0.1,  # More deterministic for reports
            "timeout": 60  # Longer timeout for report generation
        }]
        
        # System message for report generation
        system_message = """You are a report generator for Excel data analysis.

Your job:
1. Interpret vague report titles and determine logic
2. Generate report configurations with filters, grouping, formatting
3. Use report_builder.py for assembly
4. Return structured report results

Always return JSON with:
- report_name: Name of the report
- sql: SQL query for data extraction
- filters: Applied filters
- group_by: Grouping fields
- format: Output format (table, chart)
- output_type: Output type (html, xlsx, json)
- summary: Report description

Be precise with report logic and handle edge cases gracefully."""

        try:
            super().__init__(
                name=name,
                llm_config={"config_list": config_list},
                system_message=system_message,
                human_input_mode="NEVER",  # Automated for POC
                max_consecutive_auto_reply=3
            )
            logger.info(f"ReportAgent '{name}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ReportAgent: {e}")
            raise

    async def process_report_request(self, structured_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process report request and generate report
        
        Args:
            structured_input (Dict[str, Any]): Structured input containing:
                - doc_id: Document identifier
                - query_text: User's natural language report request
                - context: Schema, metadata, etc.
                - datetime_context: Time context
                
        Returns:
            Dict[str, Any]: Report results with HTML, XLSX, or JSON output
        """
        try:
            # Extract input data
            doc_id = structured_input.get("doc_id", "")
            query_text = structured_input.get("query_text", "")
            context = structured_input.get("context", {})
            datetime_context = structured_input.get("datetime_context", {})
            
            logger.info(f"ReportAgent processing report request for doc_id: {doc_id}")
            logger.info(f"Report request: {query_text[:100]}...")
            
            # Load document metadata
            metadata = load_metadata(doc_id)
            if not metadata:
                return {
                    "success": False,
                    "error": f"No metadata found for doc_id: {doc_id}",
                    "report_name": "temp_report",
                    "output": "",
                    "summary": "Report failed - document not found"
                }
            
            # Get schema and table information
            schema = context.get("schema", metadata.get("fields", []))
            duckdb_table_name = context.get("duckdb_table_name", metadata.get("duckdb_table_name", ""))
            record_count = context.get("record_count", metadata.get("record_count", 0))
            
            # Generate report configuration using LLM
            report_config = self._generate_report_config(query_text, schema, metadata, datetime_context, duckdb_table_name)
            
            if not report_config.get("success", False):
                return report_config
            
            # Build report using report_builder
            report_result = self._build_report(report_config["config"], duckdb_table_name)
            
            if not report_result.get("success", False):
                return report_result
            
            # Prepare final result
            report_output = {
                "success": True,
                "report_name": report_config["config"]["report_name"],
                "sql": report_config["config"]["sql"],
                "filters": report_config["config"]["filters"],
                "group_by": report_config["config"]["group_by"],
                "format": report_config["config"]["format"],
                "output_type": report_config["config"]["output_type"],
                "output": report_result["output"],
                "summary": report_result["summary"],
                "doc_id": doc_id,
                "query_text": query_text,
                "generation_time": datetime_context.get("now", "unknown")
            }
            
            # Auto-save report with intelligent classification
            await self._save_report_automatically(report_output, doc_id)
            
            logger.info(f"ReportAgent completed successfully for doc_id: {doc_id}")
            return report_output
            
        except Exception as e:
            logger.error(f"Error in ReportAgent processing: {e}")
            return {
                "success": False,
                "error": f"Report processing failed: {str(e)}",
                "report_name": "temp_report",
                "output": "",
                "summary": "Report failed due to processing error"
            }

    def _generate_report_config(self, query_text: str, schema: List[str], metadata: Dict[str, Any], 
                              datetime_context: Dict[str, Any], table_name: str) -> Dict[str, Any]:
        """
        Generate report configuration using LLM
        
        Args:
            query_text (str): User's natural language report request
            schema (List[str]): Available fields
            metadata (Dict[str, Any]): Document metadata
            datetime_context (Dict[str, Any]): Time context
            table_name (str): DuckDB table name
            
        Returns:
            Dict[str, Any]: Report configuration result
        """
        try:
            # For POC, we'll use a simplified report configuration generation
            # In production, this would use the agent's LLM
            report_config = self._simple_report_config_generation(query_text, schema, table_name)
            
            return {
                "success": True,
                "config": report_config
            }
            
        except Exception as e:
            logger.error(f"Error generating report config: {e}")
            return {
                "success": False,
                "error": f"Report config generation failed: {str(e)}"
            }

    def _simple_report_config_generation(self, query_text: str, schema: List[str], table_name: str) -> Dict[str, Any]:
        """
        Simple report configuration generation for POC (replace with LLM in production)
        
        Args:
            query_text (str): User report request
            schema (List[str]): Available fields
            table_name (str): Table name
            
        Returns:
            Dict[str, Any]: Report configuration
        """
        query_lower = query_text.lower()
        
        # Simple pattern matching for common report types
        if "summary" in query_lower or "overview" in query_lower:
            # Look for amount/cost fields for summary
            amount_fields = [field for field in schema if any(word in field.lower() for word in ["amount", "cost", "price", "value"])]
            if amount_fields:
                return {
                    "report_name": "Summary Report",
                    "sql": f"SELECT SUM({amount_fields[0]}) as total FROM {table_name}",
                    "filters": {},
                    "group_by": [],
                    "format": "table",
                    "output_type": "html",
                    "chart": "",
                    "description": "Summary of total amounts"
                }
        
        if "weekly" in query_lower or "monthly" in query_lower:
            # Look for date fields
            date_fields = [field for field in schema if any(word in field.lower() for word in ["date", "time", "week", "month"])]
            if date_fields:
                return {
                    "report_name": "Time-based Report",
                    "sql": f"SELECT {date_fields[0]}, COUNT(*) as count FROM {table_name} GROUP BY {date_fields[0]}",
                    "filters": {},
                    "group_by": [date_fields[0]],
                    "format": "chart",
                    "output_type": "html",
                    "chart": "bar",
                    "description": "Time-based analysis"
                }
        
        # Default: simple count report
        return {
            "report_name": "Basic Report",
            "sql": f"SELECT COUNT(*) as count FROM {table_name}",
            "filters": {},
            "group_by": [],
            "format": "table",
            "output_type": "html",
            "chart": "",
            "description": "Basic record count report"
        }

    def _build_report(self, report_config: Dict[str, Any], table_name: str) -> Dict[str, Any]:
        """
        Build report using report_builder utility
        
        Args:
            report_config (Dict[str, Any]): Report configuration
            table_name (str): Table name
            
        Returns:
            Dict[str, Any]: Report build results
        """
        try:
            # Connect to DuckDB
            conn = duckdb.connect("excel_reporting.db")
            
            # Build report using report_builder
            result = build_report(
                conn=conn,
                table_name=table_name,
                report_config=report_config,
                output_type=report_config.get("output_type", "html")
            )
            
            conn.close()
            
            return {
                "success": True,
                "output": result.get("output", ""),
                "summary": result.get("summary", "Report generated successfully")
            }
            
        except Exception as e:
            logger.error(f"Error building report: {e}")
            return {
                "success": False,
                "error": f"Report building failed: {str(e)}",
                "output": "",
                "summary": "Report building failed"
            }

    async def _save_report_automatically(self, report_result: Dict[str, Any], doc_id: str):
        """
        Automatically save report with intelligent classification
        
        Args:
            report_result (Dict[str, Any]): Report results
            doc_id (str): Document identifier
        """
        try:
            # Load document metadata for classification
            doc_metadata = load_metadata(doc_id)
            if not doc_metadata:
                logger.error(f"No metadata found for doc_id: {doc_id}")
                return
                
            # Extract document type information for intelligent classification
            document_type = doc_metadata.get("document_type", "Unknown")
            document_type_code = doc_metadata.get("document_type_code", "UNK")
            sql_query = report_result.get("sql", "")
            report_text = report_result.get("query_text", "")
            
            # Check SQL uniqueness within document type
            conn = duckdb.connect("excel_reporting.db")
            uniqueness_result = check_sql_uniqueness(conn, sql_query, document_type_code)
            
            # Generate intelligent report name based on uniqueness
            if uniqueness_result["is_unique"]:
                # Generate LLM name for unique reports
                from app import generate_report_name_with_llm
                naming_result = await generate_report_name_with_llm(
                    sql_query, report_text, document_type, document_type_code
                )
                report_name = naming_result["report_name"]
                description = naming_result["description"]
            else:
                # Use existing report name for duplicates
                existing_report = uniqueness_result["existing_query"]
                report_name = f"temp_report_{doc_id}_{int(time.time())}"
                description = f"Local copy of: {existing_report['report_name']}"
            
            # Save report with intelligent classification
            save_success = save_report(
                conn=conn,
                doc_id=doc_id,
                document_type=document_type,
                document_type_code=document_type_code,
                report_name=report_name,
                sql=sql_query,
                filters=report_result.get("filters", {}),
                group_by=report_result.get("group_by", []),
                format=report_result.get("format", "table"),
                chart=report_result.get("chart", ""),
                output_type=report_result.get("output_type", "html"),
                sql_hash=uniqueness_result["sql_hash"],
                is_global=uniqueness_result["is_unique"],
                tags=["auto_saved"],
                description=description
            )
            conn.close()
            
            if save_success:
                # Append to JSON metadata with summary
                report_data = {
                    "report_name": report_name,
                    "sql": sql_query,
                    "filters": report_result.get("filters", {}),
                    "group_by": report_result.get("group_by", []),
                    "format": report_result.get("format", "table"),
                    "chart": report_result.get("chart", ""),
                    "output_type": report_result.get("output_type", "html"),
                    "summary": report_result.get("summary", ""),  # Include summary
                    "timestamp": report_result.get("generation_time", ""),
                    "auto_saved": True
                }
                append_report_to_metadata(doc_id, report_data)
                logger.info(f"Report auto-saved as '{report_name}' for doc_id: {doc_id}")
            else:
                logger.warning(f"Failed to auto-save report for doc_id: {doc_id}")
                
        except Exception as e:
            logger.error(f"Error in intelligent report classification: {e}")

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent for debugging/monitoring
        
        Returns:
            Dict[str, Any]: Agent information
        """
        return {
            "name": self.name,
            "type": "ConversableAgent",
            "purpose": "Interpret and build grouped/filtered reports",
            "capabilities": [
                "Report configuration generation",
                "Report building with multiple output formats",
                "Automatic report saving",
                "Chart and visualization support"
            ],
            "llm_config": self.llm_config
        }

def create_report_agent(name: str = "ReportAgent") -> ReportAgent:
    """
    Factory function to create a ReportAgent instance
    
    Args:
        name (str): Agent name identifier
        
    Returns:
        ReportAgent: Configured ReportAgent instance
    """
    try:
        agent = ReportAgent(name=name)
        logger.info(f"ReportAgent '{name}' created successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to create ReportAgent: {e}")
        raise

# Example usage and testing
if __name__ == "__main__":
    # Test ReportAgent creation and basic functionality
    try:
        # Create agent
        report_agent = create_report_agent()
        
        # Test with sample input
        sample_input = {
            "doc_id": "hospital_ledger_fy2024_001",
            "query_text": "Generate a weekly spending summary",
            "context": {
                "schema": ["Vendor", "Date", "Amount"],
                "record_count": 1200,
                "duckdb_table_name": "hospital_ledger_fy2024_001"
            },
            "datetime_context": {"now": "2025-09-02"}
        }
        
        # Process report request
        report_result = report_agent.process_report_request(sample_input)
        
        print("=== ReportAgent Test Results ===")
        print(f"Agent Info: {report_agent.get_agent_info()}")
        print(f"Report Result: {json.dumps(report_result, indent=2, default=str)}")
        
    except Exception as e:
        print(f"ReportAgent test failed: {e}")
