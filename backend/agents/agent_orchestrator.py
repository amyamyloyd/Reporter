"""
Agent Orchestrator - Main Entry Point for AutoGen Agent System
AutoGen Excel Intelligence System - Phase 3

This module provides the main entry point for the AutoGen agent system.
It coordinates between ChatAgent, OrchestrationAgent, and downstream agents.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# Import our agents
from agents.chat_agent import create_chat_agent
from agents.orchestration_agent import create_orchestration_agent
from agents.query_agent import create_query_agent
from agents.report_agent import create_report_agent
from agents.upload_agent import create_upload_agent
from agents.memory_agent import create_memory_agent

# Configure logging
logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Main orchestrator for the AutoGen agent system
    
    Responsibilities:
    - Initialize all agents
    - Coordinate agent conversations
    - Handle frontend requests
    - Manage agent state
    """
    
    def __init__(self):
        """Initialize the agent orchestrator with all agents"""
        try:
            # Create all agents
            self.chat_agent = create_chat_agent("ChatAgent")
            self.orchestration_agent = create_orchestration_agent("OrchestrationAgent")
            self.query_agent = create_query_agent("QueryAgent")
            self.report_agent = create_report_agent("ReportAgent")
            self.upload_agent = create_upload_agent("UploadAgent")
            self.memory_agent = create_memory_agent("MemoryAgent")
            
            # Agent registry for routing
            self.agent_registry = {
                "QueryAgent": self.query_agent,
                "ReportAgent": self.report_agent,
                "UploadAgent": self.upload_agent,
                "MemoryAgent": self.memory_agent
            }
            
            logger.info("AgentOrchestrator initialized successfully with all agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize AgentOrchestrator: {e}")
            raise

    async def process_user_message(self, user_input: str, localStorage_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process user message through the complete agent pipeline
        
        Args:
            user_input (str): User's natural language input
            localStorage_context (Dict[str, Any]): Context from frontend localStorage
            
        Returns:
            Dict[str, Any]: Complete response from the agent system
        """
        try:
            logger.info(f"Processing user message: {user_input[:100]}...")
            
            # Step 1: ChatAgent processes natural language input
            structured_input = self.chat_agent.process_user_input(user_input, localStorage_context)
            logger.info(f"ChatAgent structured input: {structured_input['doc_id']}")
            
            # Step 2: OrchestrationAgent routes to appropriate agent
            routing_result = self.orchestration_agent.route_request_to_agent(structured_input)
            target_agent_name = routing_result["target_agent"]
            logger.info(f"OrchestrationAgent routed to: {target_agent_name}")
            
            # Step 3: Execute with target agent
            if target_agent_name in self.agent_registry:
                target_agent = self.agent_registry[target_agent_name]
                
                # Route to appropriate agent method
                if target_agent_name == "QueryAgent":
                    result = await target_agent.process_query_request(structured_input)
                elif target_agent_name == "ReportAgent":
                    result = target_agent.process_report_request(structured_input)
                elif target_agent_name == "UploadAgent":
                    result = target_agent.process_upload_request(structured_input)
                elif target_agent_name == "MemoryAgent":
                    result = target_agent.process_memory_request(structured_input)
                else:
                    result = {"success": False, "error": f"Unknown agent: {target_agent_name}"}
                
                # Add routing metadata to result
                result["routing_info"] = {
                    "target_agent": target_agent_name,
                    "routing_confidence": routing_result.get("routing_confidence", 0.5),
                    "routing_timestamp": routing_result.get("routing_timestamp", "")
                }
                
                logger.info(f"Agent {target_agent_name} completed successfully")
                return result
            else:
                return {
                    "success": False,
                    "error": f"Target agent not found: {target_agent_name}",
                    "routing_info": routing_result
                }
                
        except Exception as e:
            logger.error(f"Error in agent orchestration: {e}")
            return {
                "success": False,
                "error": f"Agent orchestration failed: {str(e)}",
                "routing_info": {"target_agent": "unknown", "routing_confidence": 0.0}
            }

    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all agents
        
        Returns:
            Dict[str, Any]: Status information for all agents
        """
        try:
            return {
                "orchestrator_status": "active",
                "agents": {
                    "ChatAgent": self.chat_agent.get_agent_info(),
                    "OrchestrationAgent": self.orchestration_agent.get_agent_info(),
                    "QueryAgent": self.query_agent.get_agent_info(),
                    "ReportAgent": self.report_agent.get_agent_info(),
                    "UploadAgent": self.upload_agent.get_agent_info(),
                    "MemoryAgent": self.memory_agent.get_agent_info()
                },
                "agent_registry": list(self.agent_registry.keys())
            }
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {"orchestrator_status": "error", "error": str(e)}

# Global orchestrator instance
_agent_orchestrator = None

def get_agent_orchestrator() -> AgentOrchestrator:
    """
    Get the global agent orchestrator instance (singleton pattern)
    
    Returns:
        AgentOrchestrator: Global orchestrator instance
    """
    global _agent_orchestrator
    if _agent_orchestrator is None:
        _agent_orchestrator = AgentOrchestrator()
    return _agent_orchestrator

# Example usage and testing
if __name__ == "__main__":
    # Test AgentOrchestrator creation and basic functionality
    try:
        # Create orchestrator
        orchestrator = get_agent_orchestrator()
        
        # Test with sample input
        sample_input = "How much did we spend on Vendor X in Q2?"
        sample_context = {
            "doc_id": "hospital_ledger_fy2024_001",
            "schema": ["Vendor", "Date", "Amount"],
            "record_count": 1200,
            "duckdb_table_name": "hospital_ledger_fy2024_001"
        }
        
        # Process message (async in real usage)
        import asyncio
        result = asyncio.run(orchestrator.process_user_message(sample_input, sample_context))
        
        print("=== AgentOrchestrator Test Results ===")
        print(f"Agent Status: {orchestrator.get_agent_status()}")
        print(f"Processing Result: {json.dumps(result, indent=2, default=str)}")
        
    except Exception as e:
        print(f"AgentOrchestrator test failed: {e}")
