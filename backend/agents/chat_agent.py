"""
ChatAgent - First Interface with User
AutoGen Excel Intelligence System - Phase 3

This agent serves as the entry point for user interactions.
It accepts natural language input from the frontend and structures it
for routing to the OrchestrationAgent.

Type: ConversableAgent
Purpose: Parse user input and inject localStorage context
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Import AutoGen components
try:
    from autogen import ConversableAgent
except ImportError as e:
    logging.error(f"Failed to import AutoGen components: {e}")
    raise

# Configure logging
logger = logging.getLogger(__name__)

class ChatAgent(ConversableAgent):
    """
    ChatAgent - First interface with user for natural language processing
    
    Responsibilities:
    - Accept natural language input from frontend
    - Parse prompt into structured dict with doc_id, query_text, context
    - Inject localStorage context (schema, record count, duckdb table location)
    - Send structured request to OrchestrationAgent
    """
    
    def __init__(self, name: str = "ChatAgent"):
        """
        Initialize ChatAgent with AutoGen configuration
        
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
        
        # System message for natural language processing
        system_message = """You are a natural language processor for Excel data analysis.

Your job:
1. Accept user's natural language input
2. Extract key information: doc_id, query_text, intent
3. Structure the input for routing to appropriate agents
4. Inject context from localStorage (schema, metadata)

Always return structured JSON with:
- doc_id: Document identifier
- query_text: User's original question/request
- intent: Detected intent (query, report, upload, memory)
- context: Additional context information
- datetime_context: Current time context

Be conversational but focused on structuring the input properly."""

        try:
            super().__init__(
                name=name,
                llm_config={"config_list": config_list},
                system_message=system_message,
                human_input_mode="NEVER",  # Automated for POC
                max_consecutive_auto_reply=3
            )
            logger.info(f"ChatAgent '{name}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChatAgent: {e}")
            raise

    def process_user_input(self, user_input: str, localStorage_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process natural language input and structure it for routing
        
        Args:
            user_input (str): User's natural language input
            localStorage_context (Dict[str, Any]): Context from frontend localStorage
            
        Returns:
            Dict[str, Any]: Structured input for OrchestrationAgent
        """
        try:
            # Default context if none provided
            if localStorage_context is None:
                localStorage_context = {}
            
            # Build structured input
            structured_input = {
                "doc_id": localStorage_context.get("doc_id", ""),
                "query_text": user_input,
                "intent": "",  # Will be detected by OrchestrationAgent
                "context": {
                    "schema": localStorage_context.get("schema", []),
                    "record_count": localStorage_context.get("record_count", 0),
                    "duckdb_table_name": localStorage_context.get("duckdb_table_name", ""),
                    "metadata": localStorage_context.get("metadata", {}),
                    "recent_uploads": localStorage_context.get("recentUploads", []),
                    "conversation_id": localStorage_context.get("conversation_id", "")
                },
                "datetime_context": {
                    "now": datetime.now().isoformat(),
                    "current_quarter": self._get_current_quarter(),
                    "last_quarter": self._get_last_quarter()
                }
            }
            
            logger.info(f"ChatAgent processed input for doc_id: {structured_input['doc_id']}")
            logger.info(f"Query text: {user_input[:100]}...")
            
            return structured_input
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            # Return minimal structured input on error
            return {
                "doc_id": "",
                "query_text": user_input,
                "intent": "query",  # Safe fallback
                "context": {},
                "datetime_context": {"now": datetime.now().isoformat()}
            }

    def _get_current_quarter(self) -> str:
        """Get current quarter string (Q1, Q2, Q3, Q4)"""
        month = datetime.now().month
        if month <= 3:
            return "Q1"
        elif month <= 6:
            return "Q2"
        elif month <= 9:
            return "Q3"
        else:
            return "Q4"

    def _get_last_quarter(self) -> str:
        """Get last quarter string"""
        current = self._get_current_quarter()
        quarter_map = {"Q1": "Q4", "Q2": "Q1", "Q3": "Q2", "Q4": "Q3"}
        return quarter_map.get(current, "Q4")

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent for debugging/monitoring
        
        Returns:
            Dict[str, Any]: Agent information
        """
        return {
            "name": self.name,
            "type": "ConversableAgent",
            "purpose": "First interface with user for natural language processing",
            "capabilities": [
                "Natural language input processing",
                "Context injection from localStorage",
                "Structured output for routing",
                "Intent detection preparation"
            ],
            "llm_config": self.llm_config
        }

def create_chat_agent(name: str = "ChatAgent") -> ChatAgent:
    """
    Factory function to create a ChatAgent instance
    
    Args:
        name (str): Agent name identifier
        
    Returns:
        ChatAgent: Configured ChatAgent instance
    """
    try:
        agent = ChatAgent(name=name)
        logger.info(f"ChatAgent '{name}' created successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to create ChatAgent: {e}")
        raise

# Example usage and testing
if __name__ == "__main__":
    # Test ChatAgent creation and basic functionality
    try:
        # Create agent
        chat_agent = create_chat_agent()
        
        # Test with sample input
        sample_input = "How much did we spend on Vendor X in Q2?"
        sample_context = {
            "doc_id": "hospital_ledger_fy2024_001",
            "schema": ["Vendor", "Date", "Amount"],
            "record_count": 1200,
            "duckdb_table_name": "hospital_ledger_fy2024_001"
        }
        
        # Process input
        structured_output = chat_agent.process_user_input(sample_input, sample_context)
        
        print("=== ChatAgent Test Results ===")
        print(f"Agent Info: {chat_agent.get_agent_info()}")
        print(f"Structured Output: {json.dumps(structured_output, indent=2)}")
        
    except Exception as e:
        print(f"ChatAgent test failed: {e}")
