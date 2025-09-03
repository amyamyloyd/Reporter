"""
OrchestrationAgent - Central Router
AutoGen Excel Intelligence System - Phase 3

This agent serves as the central router that receives structured input
from ChatAgent and routes it to the appropriate downstream agent.

Type: ToolAgent
Purpose: Route intent to proper downstream agent
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
from utils.agent_router import route_request

# Configure logging
logger = logging.getLogger(__name__)

class OrchestrationAgent(ConversableAgent):
    """
    OrchestrationAgent - Central router for agent coordination
    
    Responsibilities:
    - Accept structured dict from ChatAgent
    - Call route_request() from agent_router.py
    - Route to: QueryAgent, ReportAgent, UploadAgent, MemoryAgent
    - Use LLM for disambiguation if unclear
    - Enforce fallback names: temp_query, temp_report
    """
    
    def __init__(self, name: str = "OrchestrationAgent"):
        """
        Initialize OrchestrationAgent with AutoGen configuration
        
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
        
        # System message for orchestration and routing
        system_message = """You are the central orchestrator for Excel data analysis agents.

Your job:
1. Receive structured input from ChatAgent
2. Use route_request() to determine target agent
3. Route to appropriate agent: QueryAgent, ReportAgent, UploadAgent, MemoryAgent
4. Handle disambiguation when intent is unclear
5. Enforce fallback names: temp_query, temp_report

Always return the name of the target agent and any routing context needed."""

        try:
            super().__init__(
                name=name,
                llm_config={"config_list": config_list},
                system_message=system_message,
                human_input_mode="NEVER",  # Automated for POC
                max_consecutive_auto_reply=3
            )
            logger.info(f"OrchestrationAgent '{name}' initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OrchestrationAgent: {e}")
            raise

    def route_request_to_agent(self, structured_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route structured input to appropriate agent
        
        Args:
            structured_input (Dict[str, Any]): Structured input from ChatAgent containing:
                - doc_id: Document identifier
                - query_text: User's natural language input
                - intent: Optional explicit intent
                - context: Additional context information
                - datetime_context: Time context
                
        Returns:
            Dict[str, Any]: Routing decision with target agent and context
        """
        try:
            # Use agent_router to determine target agent
            target_agent = route_request(structured_input)
            
            # Add routing metadata
            routing_result = {
                "target_agent": target_agent,
                "routing_confidence": self._calculate_routing_confidence(structured_input, target_agent),
                "structured_input": structured_input,
                "routing_timestamp": json.dumps({"timestamp": "now"}, default=str),
                "fallback_names": {
                    "query": "temp_query",
                    "report": "temp_report"
                }
            }
            
            logger.info(f"OrchestrationAgent routed to: {target_agent}")
            logger.info(f"Routing confidence: {routing_result['routing_confidence']}")
            
            return routing_result
            
        except Exception as e:
            logger.error(f"Error in orchestration routing: {e}")
            # Safe fallback to QueryAgent
            return {
                "target_agent": "QueryAgent",
                "routing_confidence": 0.5,
                "structured_input": structured_input,
                "routing_timestamp": json.dumps({"timestamp": "now"}, default=str),
                "fallback_names": {
                    "query": "temp_query",
                    "report": "temp_report"
                },
                "error": str(e)
            }

    def _calculate_routing_confidence(self, structured_input: Dict[str, Any], target_agent: str) -> float:
        """
        Calculate confidence score for routing decision
        
        Args:
            structured_input (Dict[str, Any]): Input data
            target_agent (str): Selected target agent
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        try:
            # Import confidence calculation from agent_router
            from utils.agent_router import get_routing_confidence
            return get_routing_confidence(structured_input)
        except Exception as e:
            logger.warning(f"Could not calculate routing confidence: {e}")
            return 0.7  # Default confidence

    def handle_disambiguation(self, structured_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle cases where intent is unclear using LLM disambiguation
        
        Args:
            structured_input (Dict[str, Any]): Input data
            
        Returns:
            Dict[str, Any]: Disambiguation result with clearer intent
        """
        try:
            # Build disambiguation prompt
            disambiguation_prompt = f"""
            The user's intent is unclear. Please analyze and clarify:
            
            Query: {structured_input.get('query_text', '')}
            Context: {structured_input.get('context', {})}
            
            Determine if this is a:
            1. Query (data question) - route to QueryAgent
            2. Report (summary/chart) - route to ReportAgent  
            3. Upload (file metadata) - route to UploadAgent
            4. Memory (saved items) - route to MemoryAgent
            
            Respond with JSON:
            {{
                "intent": "query|report|upload|memory",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation"
            }}
            """
            
            # Use LLM for disambiguation (simplified for POC)
            # In a full implementation, this would use the agent's LLM
            disambiguation_result = {
                "intent": "query",  # Default fallback
                "confidence": 0.6,
                "reasoning": "Default fallback to query for unclear intent"
            }
            
            # Update structured input with clarified intent
            structured_input["intent"] = disambiguation_result["intent"]
            
            logger.info(f"Disambiguation result: {disambiguation_result}")
            return structured_input
            
        except Exception as e:
            logger.error(f"Error in disambiguation: {e}")
            # Return original input with default intent
            structured_input["intent"] = "query"
            return structured_input

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent for debugging/monitoring
        
        Returns:
            Dict[str, Any]: Agent information
        """
        return {
            "name": self.name,
            "type": "ConversableAgent",
            "purpose": "Central router for agent coordination",
            "capabilities": [
                "Request routing to appropriate agents",
                "Intent disambiguation using LLM",
                "Fallback name enforcement",
                "Routing confidence calculation"
            ],
            "target_agents": ["QueryAgent", "ReportAgent", "UploadAgent", "MemoryAgent"],
            "llm_config": self.llm_config
        }

def create_orchestration_agent(name: str = "OrchestrationAgent") -> OrchestrationAgent:
    """
    Factory function to create an OrchestrationAgent instance
    
    Args:
        name (str): Agent name identifier
        
    Returns:
        OrchestrationAgent: Configured OrchestrationAgent instance
    """
    try:
        agent = OrchestrationAgent(name=name)
        logger.info(f"OrchestrationAgent '{name}' created successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to create OrchestrationAgent: {e}")
        raise

# Example usage and testing
if __name__ == "__main__":
    # Test OrchestrationAgent creation and basic functionality
    try:
        # Create agent
        orchestration_agent = create_orchestration_agent()
        
        # Test with sample input
        sample_input = {
            "doc_id": "hospital_ledger_fy2024_001",
            "query_text": "How much did we spend on Vendor X in Q2?",
            "context": {
                "schema": ["Vendor", "Date", "Amount"],
                "record_count": 1200
            },
            "datetime_context": {"now": "2025-09-02"}
        }
        
        # Route request
        routing_result = orchestration_agent.route_request_to_agent(sample_input)
        
        print("=== OrchestrationAgent Test Results ===")
        print(f"Agent Info: {orchestration_agent.get_agent_info()}")
        print(f"Routing Result: {json.dumps(routing_result, indent=2)}")
        
    except Exception as e:
        print(f"OrchestrationAgent test failed: {e}")
