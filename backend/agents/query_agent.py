
"""
QueryAgent - Convert Query Intent into SQL + Response
AutoGen Excel Intelligence System - Phase 3

This agent converts user query intent into SQL queries and executes them
via DuckDB, returning structured results.

Type: ConversableAgent
Purpose: Convert query intent into SQL + response
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
from utils.duckdb_manager import get_query_by_name, save_query, check_sql_uniqueness
from utils.json_store import load_metadata, append_query_to_metadata

# Configure logging
logger = logging.getLogger(__name__)

class QueryAgent(ConversableAgent):
    """
    QueryAgent - Convert query intent into SQL and execute via DuckDB
    
    Responsibilities:
    - Receive: doc_id, query_text, schema, metadata
    - Prompt LLM with full schema, user question, document metadata
    - Execute SQL via DuckDB
    - Return: sql, rows, columns, summary
    - Auto-save as temp_query unless named
    """
    
    def __init__(self, name: str = "QueryAgent"):
        """
        Initialize QueryAgent with AutoGen configuration
        
        Args:
            name (str): Agent name identifier
        """
        # AutoGen 0.4.0+ configuration - cost-optimized as per rules
        config_list = [{
            "model": "gpt-4",  # Cost-optimized
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "max_tokens": 1000,  # More tokens for SQL generation
            "temperature": 0.1,  # More deterministic for SQL
            "timeout": 60  # Longer timeout for SQL execution
        }]
        
        # Store context for clarification follow-ups
        self.query_context = {}
        
        # System message for SQL generation and execution
        system_message = """You are a SQL query generator for Excel data analysis.

Your job:
1. Receive user questions about Excel data
2. Generate accurate SQL queries based on schema and metadata
3. Execute queries via DuckDB
4. Return structured results with summary

Always return JSON with:
- sql: The generated SQL query
- rows: Query results as array of arrays
- columns: Column names
- summary: Natural language summary of results

Be precise with SQL syntax and handle edge cases gracefully."""

        try:
            super().__init__(
                name=name,
                llm_config={"config_list": config_list},
                system_message=system_message,
                human_input_mode="NEVER",  # Automated for POC
                max_consecutive_auto_reply=3
            )
            logger.info(f"QueryAgent '{name}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize QueryAgent: {e}")
            raise

    async def process_query_request(self, structured_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process query request and execute SQL
        
        Args:
            structured_input (Dict[str, Any]): Structured input containing:
                - doc_id: Document identifier
                - query_text: User's natural language query
                - context: Schema, metadata, etc.
                - datetime_context: Time context
                
        Returns:
            Dict[str, Any]: Query results with SQL, rows, columns, summary
        """
        try:
            # Extract input data
            doc_id = structured_input.get("doc_id", "")
            query_text = structured_input.get("query_text", "")
            context = structured_input.get("context", {})
            datetime_context = structured_input.get("datetime_context", {})
            
            logger.info(f"QueryAgent processing query for doc_id: {doc_id}")
            logger.info(f"Query text: {query_text[:100]}...")
            
            # Load document metadata
            metadata = load_metadata(doc_id)
            if not metadata:
                return {
                    "success": False,
                    "error": f"No metadata found for doc_id: {doc_id}",
                    "sql": "",
                    "rows": [],
                    "columns": [],
                    "summary": "Query failed - document not found"
                }
            
            # Get schema and table information
            schema = context.get("schema", metadata.get("fields", []))
            duckdb_table_name = context.get("duckdb_table_name", metadata.get("duckdb_table_name", ""))
            record_count = context.get("record_count", metadata.get("record_count", 0))
            
            # Ensure we have the correct table name
            if not duckdb_table_name:
                logger.error(f"No duckdb_table_name found for doc_id: {doc_id}")
                return {
                    "success": False,
                    "error": f"No DuckDB table name found for doc_id: {doc_id}",
                    "sql": "",
                    "rows": [],
                    "columns": [],
                    "summary": "Query failed - no table name found"
                }
            
            logger.info(f"Using DuckDB table name: {duckdb_table_name}")
            
            # Generate SQL using LLM
            sql_result = self._generate_sql(query_text, schema, metadata, datetime_context, duckdb_table_name, doc_id)
            
            if not sql_result.get("success", False):
                return sql_result
            
            # Check if this is a clarification request instead of SQL
            if "clarification" in sql_result and sql_result["clarification"]:
                return {
                    "success": True,
                    "clarification": sql_result["clarification"],
                    "doc_id": doc_id,
                    "query_text": query_text,
                    "routing_info": {"target_agent": "QueryAgent", "routing_confidence": 0.8}
                }
            
            sql_query = sql_result["sql"]
            
            # Execute SQL via DuckDB
            execution_result = self._execute_sql(sql_query, duckdb_table_name)
            
            if not execution_result.get("success", False):
                return execution_result
            
            # Generate summary
            summary = self._generate_summary(query_text, execution_result, sql_query)
            
            # Determine result management strategy
            row_count = len(execution_result["rows"])
            result_management = self._determine_result_management(row_count, execution_result["rows"], execution_result["columns"], doc_id, query_text)
            
            # Prepare final result
            query_result = {
                "success": True,
                "sql": sql_query,
                "rows": execution_result["rows"],
                "columns": execution_result["columns"],
                "summary": summary,
                "doc_id": doc_id,
                "query_text": query_text,
                "execution_time": datetime_context.get("now", "unknown"),
                "result_management": result_management
            }
            
            # Auto-save query with intelligent classification
            await self._save_query_automatically(query_result, doc_id)
            
            logger.info(f"QueryAgent completed successfully for doc_id: {doc_id}")
            return query_result
            
        except Exception as e:
            logger.error(f"Error in QueryAgent processing: {e}")
            return {
                "success": False,
                "error": f"Query processing failed: {str(e)}",
                "sql": "",
                "rows": [],
                "columns": [],
                "summary": "Query failed due to processing error"
            }

    def _generate_sql(self, query_text: str, schema: List[str], metadata: Dict[str, Any], 
                     datetime_context: Dict[str, Any], table_name: str, doc_id: str = "") -> Dict[str, Any]:
        """
        Generate SQL query using LLM with fallback to simple patterns
        
        Args:
            query_text (str): User's natural language query
            schema (List[str]): Available fields
            metadata (Dict[str, Any]): Document metadata
            datetime_context (Dict[str, Any]): Time context
            table_name (str): DuckDB table name
            
        Returns:
            Dict[str, Any]: SQL generation result
        """
        try:
            # Check if query is ambiguous first
            is_ambiguous = self._is_ambiguous_query(query_text)
            logger.info(f"Ambiguity check for '{query_text}': {is_ambiguous}")
            
            if is_ambiguous:
                # Store the original query context for follow-up
                self.query_context[doc_id] = {
                    "original_query": query_text,
                    "schema": schema,
                    "table_name": table_name,
                    "metadata": metadata
                }
                logger.info(f"Query is ambiguous, requesting clarification: {query_text}")
                return {
                    "success": True,
                    "clarification": f"I need to clarify your request. Do you want to:\n1. See all the records that match your criteria (show me the data)\n2. Just count how many records match your criteria\n\nPlease specify which one you'd like!"
                }
            
            # First try simple pattern matching for common queries (performance optimization)
            simple_sql = self._simple_sql_generation(query_text, schema, table_name)
            
            # If simple pattern didn't generate a meaningful query, use LLM
            if self._is_simple_query(simple_sql, query_text):
                logger.info(f"Using simple SQL generation for: {query_text}")
                return {
                    "success": True,
                    "sql": simple_sql
                }
            else:
                # Check if this is a clarification follow-up
                if doc_id in self.query_context:
                    # This is a follow-up to an ambiguous query
                    context = self.query_context[doc_id]
                    logger.info(f"Using stored context for clarification: {query_text}")
                    return self._generate_sql_with_context(query_text, context, datetime_context)
                else:
                    # Use LLM for complex queries
                    logger.info(f"Using LLM for complex query: {query_text}")
                    return self._generate_sql_with_llm(query_text, schema, metadata, datetime_context, table_name)
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return {
                "success": False,
                "error": f"SQL generation failed: {str(e)}"
            }

    def _is_simple_query(self, sql_query: str, query_text: str) -> bool:
        """
        Check if the generated SQL is a simple pattern match or needs LLM
        
        Args:
            sql_query (str): Generated SQL query
            query_text (str): Original user query
            
        Returns:
            bool: True if simple pattern, False if needs LLM
        """
        # If SQL is just "SELECT * FROM table LIMIT 100", it's a fallback - use LLM
        if "SELECT * FROM" in sql_query and "LIMIT 100" in sql_query:
            return False
        
        # If query contains location words, names, or complex patterns, use LLM
        complex_patterns = ["find", "show", "list", "where", "in", "and", "or", "like"]
        if any(pattern in query_text.lower() for pattern in complex_patterns):
            return False
            
        return True

    def _is_ambiguous_query(self, query_text: str) -> bool:
        """
        Check if the query is ambiguous and needs clarification
        
        Args:
            query_text (str): User's natural language query
            
        Returns:
            bool: True if ambiguous, False if clear
        """
        query_lower = query_text.lower()
        
        # Ambiguous patterns that could mean "show records" OR "count records"
        ambiguous_patterns = [
            r"how many .+ are for .+",
            r"how many .+ in .+", 
            r"how many .+ with .+",
            r"how many .+ that .+",
            r"how many .+ where .+",
            r"how many .+ have .+",
            r"how many .+ contain .+",
            r"how many .+ desc .+",  # "how many cost center desc central supply"
            r"how many .+ \w+ \w+",  # "how many X Y Z" pattern
            r"how many .+ \w+$"      # "how many X Y" pattern
        ]
        
        import re
        for i, pattern in enumerate(ambiguous_patterns):
            match = re.search(pattern, query_lower)
            if match:
                logger.info(f"Ambiguous pattern {i+1} matched: '{pattern}' -> '{match.group()}'")
                return True
                
        logger.info(f"No ambiguous patterns matched for: '{query_lower}'")
        return False

    def _determine_result_management(self, row_count: int, rows: List, columns: List[str], doc_id: str, query_text: str) -> Dict[str, Any]:
        """
        Determine how to handle query results based on row count
        
        Args:
            row_count (int): Number of rows returned
            rows (List): Query result rows
            columns (List[str]): Column names
            doc_id (str): Document ID
            query_text (str): Original query text
            
        Returns:
            Dict[str, Any]: Result management strategy
        """
        try:
            if row_count <= 65:
                # Small result set - display as HTML table
                return {
                    "strategy": "html_table",
                    "row_count": row_count,
                    "display_type": "inline"
                }
            else:
                # Large result set - generate Excel file
                excel_file = self._generate_excel_file(rows, columns, doc_id, query_text)
                return {
                    "strategy": "excel_download",
                    "row_count": row_count,
                    "display_type": "download",
                    "excel_file": excel_file
                }
        except Exception as e:
            logger.error(f"Error determining result management: {e}")
            # Fallback to HTML table
            return {
                "strategy": "html_table",
                "row_count": row_count,
                "display_type": "inline",
                "error": str(e)
            }

    def _generate_excel_file(self, rows: List, columns: List[str], doc_id: str, query_text: str) -> Dict[str, Any]:
        """
        Generate Excel file for large result sets
        
        Args:
            rows (List): Query result rows
            columns (List[str]): Column names
            doc_id (str): Document ID
            query_text (str): Original query text
            
        Returns:
            Dict[str, Any]: Excel file information
        """
        try:
            import pandas as pd
            from datetime import datetime
            import os
            
            # Create DataFrame
            df = pd.DataFrame(rows, columns=columns)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c for c in query_text[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"query_results_{safe_query}_{timestamp}.xlsx"
            
            # Create output directory if it doesn't exist
            output_dir = "stored_queries/excel_exports"
            os.makedirs(output_dir, exist_ok=True)
            
            # Save Excel file
            filepath = os.path.join(output_dir, filename)
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            logger.info(f"Generated Excel file: {filepath}")
            
            return {
                "filename": filename,
                "filepath": filepath,
                "download_url": f"/download-excel/{filename}",
                "row_count": len(rows),
                "column_count": len(columns)
            }
            
        except Exception as e:
            logger.error(f"Error generating Excel file: {e}")
            return {
                "error": str(e),
                "filename": None,
                "filepath": None,
                "download_url": None
            }

    def _generate_sql_with_context(self, clarification: str, context: Dict[str, Any], datetime_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate SQL using stored context from ambiguous query
        
        Args:
            clarification (str): User's clarification (e.g., "list all matching records")
            context (Dict[str, Any]): Stored context from original ambiguous query
            datetime_context (Dict[str, Any]): Time context
            
        Returns:
            Dict[str, Any]: SQL generation result
        """
        try:
            original_query = context["original_query"]
            schema = context["schema"]
            table_name = context["table_name"]
            metadata = context["metadata"]
            
            # Build context-aware prompt
            quoted_fields = [f'"{field}"' for field in schema]
            
            llm_prompt = f"""You are generating SQL for a clarification request.

ORIGINAL AMBIGUOUS QUERY: {original_query}
USER CLARIFICATION: {clarification}
TABLE: {table_name}
AVAILABLE FIELDS: {', '.join(quoted_fields)}

Based on the original query and clarification, generate the appropriate SQL.

RULES:
1. Return ONLY the SQL query string - nothing else
2. Use EXACT field names from the schema list above
3. ALWAYS quote field names with double quotes: "Field Name"
4. Use case-insensitive matching with LOWER() function
5. Always include a LIMIT clause (max 1000 rows)

EXAMPLES:
- Original: "how many cost center desc central supply" + Clarification: "list all matching records" 
  → SELECT * FROM {table_name} WHERE LOWER("Cost Center Desc") LIKE '%central supply%' LIMIT 1000

- Original: "how many vendors in chicago" + Clarification: "just count them"
  → SELECT COUNT(*) as count FROM {table_name} WHERE LOWER("Location (city)") LIKE '%chicago%' LIMIT 1000

SQL Query:"""

            # Use the agent's LLM to generate SQL
            response = self.generate_reply(
                messages=[{"role": "user", "content": llm_prompt}],
                sender=self
            )
            
            if response:
                sql_query = response.strip()
                
                # Clean up formatting
                if sql_query.startswith("```sql"):
                    sql_query = sql_query[6:]
                if sql_query.startswith("```"):
                    sql_query = sql_query[3:]
                if sql_query.endswith("```"):
                    sql_query = sql_query[:-3]
                
                sql_query = sql_query.strip()
                
                # Check if response is JSON format
                if sql_query.startswith("{") and sql_query.endswith("}"):
                    try:
                        import json
                        json_response = json.loads(sql_query)
                        if "sql" in json_response:
                            sql_query = json_response["sql"]
                    except (json.JSONDecodeError, ValueError):
                        pass
                
                logger.info(f"Context-aware SQL generated: {sql_query}")
                
                return {
                    "success": True,
                    "sql": sql_query
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate SQL from clarification"
                }
                
        except Exception as e:
            logger.error(f"Error in context-aware SQL generation: {e}")
            return {
                "success": False,
                "error": f"Context-aware SQL generation failed: {str(e)}"
            }

    def _generate_sql_with_llm(self, query_text: str, schema: List[str], metadata: Dict[str, Any], 
                              datetime_context: Dict[str, Any], table_name: str) -> Dict[str, Any]:
        """
        Generate SQL using LLM for complex queries
        
        Args:
            query_text (str): User's natural language query
            schema (List[str]): Available fields
            metadata (Dict[str, Any]): Document metadata
            datetime_context (Dict[str, Any]): Time context
            table_name (str): DuckDB table name
            
        Returns:
            Dict[str, Any]: SQL generation result
        """
        try:
            # Build comprehensive prompt for LLM with exact field names
            quoted_fields = [f'"{field}"' for field in schema]
            logger.info(f"LLM prompt - Table name: {table_name}, Schema: {schema}")
            
            llm_prompt = f"""You are a SQL query generator. Generate ONLY a SQL query string - no JSON, no explanations, no markdown.

Question: {query_text}
Table: {table_name}
Available fields (use EXACTLY as shown): {', '.join(quoted_fields)}
Record count: {metadata.get('record_count', 0)}
Document type: {metadata.get('document_type', 'unknown')}

CRITICAL RULES:
1. Return ONLY the SQL query string - nothing else
2. Use EXACT field names from the schema list above - copy them exactly including spaces and special characters
3. ALWAYS quote field names with double quotes: "Field Name"
4. Use proper SQL syntax for DuckDB
5. ALWAYS use case-insensitive matching for text searches - use LOWER() function
6. For location/name searches, use LIKE with LOWER() for fuzzy matching: WHERE LOWER("Location (city)") LIKE '%chicago%'
7. For multiple location searches, use LOWER() with IN: WHERE LOWER("Location (city)") IN ('chicago', 'boston')
8. Handle misspellings and variations - use LIKE '%partial%' for fuzzy matching
9. Handle date/time queries appropriately
10. Use appropriate aggregation functions (SUM, COUNT, AVG, etc.)
11. Always include a LIMIT clause for large result sets (max 1000 rows)

INTENT DETECTION RULES:
- "how many X are for Y" or "how many X in Y" → AMBIGUOUS - could mean "show all X records for Y" OR "count X records for Y"
- "count of X" or "number of X" → Usually means "count the X records" (use SELECT COUNT(*) FROM table WHERE...)
- "list all X" or "show all X" → Always means "show me all X records" (use SELECT * FROM table WHERE...)
- "find X" or "get X" → Usually means "show me X records" (use SELECT * FROM table WHERE...)

CLARIFICATION RULE:
- If the query is ambiguous (like "how many X are for Y"), return a clarification message instead of SQL
- Ask the user to specify: "Do you want to see all the records, or just count how many there are?"

EXAMPLES - return ONLY the SQL string:
- "find vendors in chicago" → SELECT * FROM {table_name} WHERE LOWER("Location (city)") LIKE '%chicago%' LIMIT 1000
- "find vendors in chicago and boston" → SELECT * FROM {table_name} WHERE LOWER("Location (city)") IN ('chicago', 'boston') LIMIT 1000
- "count vendors" → SELECT COUNT(*) as count FROM {table_name} LIMIT 1000
- "show vendors by location" → SELECT "Location (city)", COUNT(*) as vendor_count FROM {table_name} GROUP BY "Location (city)" LIMIT 1000

SQL Query:"""

            # Use the agent's LLM to generate SQL
            response = self.generate_reply(
                messages=[{"role": "user", "content": llm_prompt}],
                sender=self
            )
            
            if response:
                # Extract SQL from response (clean up any formatting)
                sql_query = response.strip()
                
                # Remove markdown formatting if present
                if sql_query.startswith("```sql"):
                    sql_query = sql_query[6:]
                if sql_query.startswith("```"):
                    sql_query = sql_query[3:]
                if sql_query.endswith("```"):
                    sql_query = sql_query[:-3]
                
                sql_query = sql_query.strip()
                
                # Check if response is JSON format (fallback handling)
                if sql_query.startswith("{") and sql_query.endswith("}"):
                    try:
                        import json
                        json_response = json.loads(sql_query)
                        if "sql" in json_response:
                            sql_query = json_response["sql"]
                            logger.info(f"Extracted SQL from JSON response: {sql_query}")
                        else:
                            logger.warning("JSON response found but no 'sql' field")
                            raise ValueError("No SQL field in JSON response")
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        # Fallback to simple generation
                        return {
                            "success": True,
                            "sql": self._simple_sql_generation(query_text, schema, table_name)
                        }
                
                # Check if response is a clarification request (not SQL)
                if not sql_query.upper().startswith("SELECT") and not sql_query.upper().startswith("WITH"):
                    # This is likely a clarification message, not SQL
                    logger.info(f"LLM returned clarification: {sql_query}")
                    return {
                        "success": True,
                        "clarification": sql_query,
                        "sql": None
                    }
                
                logger.info(f"LLM generated SQL: {sql_query}")
                
                return {
                    "success": True,
                    "sql": sql_query
                }
            else:
                # Fallback to simple generation if LLM fails
                logger.warning("LLM failed to generate SQL, using fallback")
                return {
                    "success": True,
                    "sql": self._simple_sql_generation(query_text, schema, table_name)
                }
                
        except Exception as e:
            logger.error(f"Error in LLM SQL generation: {e}")
            # Fallback to simple generation
            return {
                "success": True,
                "sql": self._simple_sql_generation(query_text, schema, table_name)
            }

    def _simple_sql_generation(self, query_text: str, schema: List[str], table_name: str) -> str:
        """
        Simple SQL generation for common patterns (performance optimization)
        
        Args:
            query_text (str): User query
            schema (List[str]): Available fields
            table_name (str): Table name
            
        Returns:
            str: Generated SQL query
        """
        query_lower = query_text.lower()
        
        # Simple pattern matching for common queries
        if "total" in query_lower or "sum" in query_lower:
            # Look for amount/cost fields
            amount_fields = [field for field in schema if any(word in field.lower() for word in ["amount", "cost", "price", "value", "revenue", "discount"])]
            if amount_fields:
                return f"SELECT SUM(\"{amount_fields[0]}\") as total FROM {table_name} LIMIT 1000"
        
        if "count" in query_lower or "how many" in query_lower:
            return f"SELECT COUNT(*) as count FROM {table_name} LIMIT 1000"
        
        if "average" in query_lower or "avg" in query_lower:
            amount_fields = [field for field in schema if any(word in field.lower() for word in ["amount", "cost", "price", "value", "revenue", "discount"])]
            if amount_fields:
                return f"SELECT AVG(\"{amount_fields[0]}\") as average FROM {table_name} LIMIT 1000"
        
        # Default: return all records with limit (this triggers LLM fallback)
        return f"SELECT * FROM {table_name} LIMIT 100"

    def _execute_sql(self, sql_query: str, table_name: str) -> Dict[str, Any]:
        """
        Execute SQL query via DuckDB
        
        Args:
            sql_query (str): SQL query to execute
            table_name (str): Table name
            
        Returns:
            Dict[str, Any]: Execution results
        """
        try:
            # Connect to DuckDB
            conn = duckdb.connect("excel_reporting.db")
            
            # Execute query
            result = conn.execute(sql_query).fetchall()
            
            # Get column names
            columns = [desc[0] for desc in conn.description] if conn.description else []
            
            conn.close()
            
            return {
                "success": True,
                "rows": result,
                "columns": columns
            }
            
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            return {
                "success": False,
                "error": f"SQL execution failed: {str(e)}",
                "rows": [],
                "columns": []
            }

    def _generate_summary(self, query_text: str, execution_result: Dict[str, Any], sql_query: str) -> str:
        """
        Generate natural language summary of query results
        
        Args:
            query_text (str): Original user query
            execution_result (Dict[str, Any]): Query execution results
            sql_query (str): Executed SQL query
            
        Returns:
            str: Natural language summary
        """
        try:
            rows = execution_result.get("rows", [])
            columns = execution_result.get("columns", [])
            
            if not rows:
                return f"No results found for: {query_text}"
            
            # Simple summary generation
            if len(rows) == 1 and len(columns) == 1:
                value = rows[0][0]
                return f"The result is: {value}"
            
            if len(rows) == 1:
                return f"Found 1 result with {len(columns)} fields"
            
            return f"Found {len(rows)} results with {len(columns)} fields each"
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Query executed successfully for: {query_text}"

    async def _save_query_automatically(self, query_result: Dict[str, Any], doc_id: str):
        """
        Automatically save query using intelligent classification
        
        This method implements intelligent query classification by:
        1. Loading document metadata to get document type
        2. Checking SQL uniqueness within document type
        3. Generating LLM name for unique queries
        4. Saving with proper classification fields
        
        Args:
            query_result (Dict[str, Any]): Query results
            doc_id (str): Document identifier
        """
        try:
            # Load document metadata for classification
            doc_metadata = load_metadata(doc_id)
            if not doc_metadata:
                logger.error(f"No metadata found for doc_id: {doc_id}")
                return
                
            # Extract document type information
            document_type = doc_metadata.get("document_type", "Unknown")
            document_type_code = doc_metadata.get("document_type_code", "UNK")
            sql_query = query_result.get("sql", "")
            query_text = query_result.get("query_text", "")
            
            logger.info(f"Starting intelligent classification for document type: {document_type}")
            
            # Connect to DuckDB
            conn = duckdb.connect("excel_reporting.db")
            
            # Check SQL uniqueness within document type
            uniqueness_result = check_sql_uniqueness(conn, sql_query, document_type_code)
            
            if uniqueness_result["is_unique"]:
                # SQL is unique - generate meaningful name and save globally
                logger.info(f"✅ Unique query detected for document type: {document_type}")
                
                # Import LLM naming function
                from app import generate_query_name_with_llm
                
                naming_result = await generate_query_name_with_llm(
                    sql_query, query_text, document_type, document_type_code
                )
                
                if naming_result["success"]:
                    query_name = naming_result["query_name"]
                    description = naming_result["description"]
                    logger.info(f"LLM generated query name: {query_name}")
                else:
                    # Use fallback name when LLM fails
                    query_name = naming_result["query_name"]
                    description = naming_result["description"]
                    logger.warning(f"Using fallback query name: {query_name}")
                
                # Save globally (is_global = TRUE) for reuse across similar document types
                save_success = save_query(
                    conn=conn,
                    doc_id=doc_id,
                    document_type=document_type,
                    document_type_code=document_type_code,
                    query_name=query_name,
                    query_text=query_text,
                    sql=sql_query,
                    sql_hash=uniqueness_result["sql_hash"],
                    is_global=True,
                    tags=["auto_saved"],
                    description=description
                )
                
                if save_success:
                    logger.info(f"✅ Unique query saved globally: {query_name}")
                else:
                    logger.warning(f"Failed to save unique query: {query_name}")
                    
            else:
                # SQL already exists - save only to document-specific JSON to avoid duplicates
                existing_query = uniqueness_result["existing_query"]
                query_name = f"temp_query_{doc_id}_{int(time.time())}"
                
                logger.info(f"📋 Duplicate query detected - similar to: {existing_query['query_name']}")
                
                # Save locally only (is_global = FALSE) to avoid database bloat
                save_success = save_query(
                    conn=conn,
                    doc_id=doc_id,
                    document_type=document_type,
                    document_type_code=document_type_code,
                    query_name=query_name,
                    query_text=query_text,
                    sql=sql_query,
                    sql_hash=uniqueness_result["sql_hash"],
                    is_global=False,
                    tags=["auto_saved"],
                    description=f"Local copy of: {existing_query['query_name']}"
                )
                
                if save_success:
                    logger.info(f"📋 Duplicate query saved locally: {query_name}")
                else:
                    logger.warning(f"Failed to save duplicate query: {query_name}")
            
            conn.close()
            
            # Also append to JSON metadata with summary
            query_data = {
                "query_name": query_name,
                "query_text": query_text,
                "sql": sql_query,
                "summary": query_result.get("summary", ""),
                "timestamp": query_result.get("execution_time", ""),
                "auto_saved": True
            }
            append_query_to_metadata(doc_id, query_data)
                
        except Exception as e:
            logger.error(f"Error in intelligent query classification: {e}")

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent for debugging/monitoring
        
        Returns:
            Dict[str, Any]: Agent information
        """
        return {
            "name": self.name,
            "type": "ConversableAgent",
            "purpose": "Convert query intent into SQL and execute via DuckDB",
            "capabilities": [
                "Natural language to SQL conversion",
                "DuckDB query execution",
                "Result summarization",
                "Automatic query saving",
                "LLM fallback for complex queries"
            ],
            "llm_config": self.llm_config
        }

def create_query_agent(name: str = "QueryAgent") -> QueryAgent:
    """
    Factory function to create a QueryAgent instance
    
    Args:
        name (str): Agent name identifier
        
    Returns:
        QueryAgent: Configured QueryAgent instance
    """
    try:
        agent = QueryAgent(name=name)
        logger.info(f"QueryAgent '{name}' created successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to create QueryAgent: {e}")
        raise

# Example usage and testing
if __name__ == "__main__":
    # Test QueryAgent creation and basic functionality
    try:
        # Create agent
        query_agent = create_query_agent()
        
        # Test with sample input
        sample_input = {
            "doc_id": "hospital_ledger_fy2024_001",
            "query_text": "What is the total amount spent?",
            "context": {
                "schema": ["Vendor", "Date", "Amount"],
                "record_count": 1200,
                "duckdb_table_name": "hospital_ledger_fy2024_001"
            },
            "datetime_context": {"now": "2025-09-02"}
        }
        
        # Process query
        query_result = query_agent.process_query_request(sample_input)
        
        print("=== QueryAgent Test Results ===")
        print(f"Agent Info: {query_agent.get_agent_info()}")
        print(f"Query Result: {json.dumps(query_result, indent=2, default=str)}")
        
    except Exception as e:
        print(f"QueryAgent test failed: {e}")
