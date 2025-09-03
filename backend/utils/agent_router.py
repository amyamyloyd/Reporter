"""
Agent Router Utility for AutoGen Excel Intelligence System

This module handles routing requests to appropriate agents based on intent detection.
It analyzes user input and determines which agent should handle the request.

Key Functions:
- route_request(agent_input: Dict) -> str - Main routing function
- analyze_intent() - Intent detection logic
- validate_agent_input() - Input validation
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Configure logging for agent routing
logger = logging.getLogger(__name__)

def route_request(agent_input: Dict[str, Any]) -> str:
    """
    Route requests to appropriate agents based on intent detection
    
    Analyzes the agent input dictionary and determines which agent should
    handle the request. Returns the name of the target agent.
    
    Args:
        agent_input (Dict[str, Any]): Structured input from ChatAgent containing:
            - doc_id: Document identifier
            - query_text: User's natural language input
            - intent: Optional explicit intent
            - context: Additional context information
            
    Returns:
        str: Name of agent to route to ("QueryAgent", "ReportAgent", "UploadAgent", "MemoryAgent")
        
    Example:
        agent_name = route_request({
            "doc_id": "hospital_ledger_fy2024_001",
            "query_text": "How much did we spend on Vendor X in Q2?",
            "context": {"schema": ["Vendor", "Date", "Amount"]}
        })
        # Returns: "QueryAgent"
    """
    try:
        # Validate input
        if not validate_agent_input(agent_input):
            logger.error("Invalid agent input provided")
            return "QueryAgent"  # Default fallback
        
        # Extract key information
        query_text = agent_input.get("query_text", "").lower()
        intent = agent_input.get("intent", "").lower()
        doc_id = agent_input.get("doc_id", "")
        context = agent_input.get("context", {})
        
        logger.info(f"Routing request for doc_id: {doc_id}, query: {query_text[:50]}...")
        
        # Check for explicit intent first
        if intent:
            return route_by_explicit_intent(intent)
        
        # Analyze query text for intent patterns
        detected_intent = analyze_intent(query_text, context)
        
        # Route based on detected intent
        agent_name = route_by_detected_intent(detected_intent, query_text, context)
        
        logger.info(f"Routed to agent: {agent_name}")
        return agent_name
        
    except Exception as e:
        logger.error(f"Error in agent routing: {e}")
        return "QueryAgent"  # Safe fallback

def analyze_intent(query_text: str, context: Dict[str, Any]) -> str:
    """
    Analyze query text to detect user intent
    
    Uses pattern matching and keyword analysis to determine what the user
    is trying to accomplish.
    
    Args:
        query_text (str): User's natural language input
        context (Dict[str, Any]): Additional context information
        
    Returns:
        str: Detected intent ("query", "report", "upload", "memory", "unclear")
    """
    try:
        # Convert to lowercase for analysis
        text = query_text.lower()
        
        # Query intent patterns - asking questions, requesting data (more specific)
        query_patterns = [
            r'\b(how much|how many|what|when|where|who|which)\b.*\b(spent|spend|cost|price|amount|budget|revenue|expense|profit|loss)\b',
            r'\b(show me|find|get|list|count|sum|total|average|max|min)\b.*\b(data|records|transactions|entries|information)\b',
            r'\b(in|during|for|from|to|between|within)\b.*\b(q[1-4]|quarter|month|year|week|day)\b.*\b(spent|spend|cost|amount)\b',
            r'\b(what|which|how many)\b.*\b(vendor|client|customer|company|project|department|category)\b.*\b(spent|spend|cost|amount)\b'
        ]
        
        # Report intent patterns - requesting formatted output, summaries, charts
        report_patterns = [
            r'\b(report|summary|dashboard|chart|graph|visualization|export|download)\b',
            r'\b(weekly|monthly|quarterly|annual|yearly|periodic)\b.*\b(report|summary)\b',
            r'\b(group by|grouped|aggregated|summarized|breakdown|analysis)\b',
            r'\b(excel|xlsx|pdf|html|format|formatted)\b',
            r'\b(create|generate|build|make)\b.*\b(report|summary|dashboard)\b',
            r'\b(create|generate|build|make)\b.*\b(weekly|monthly|quarterly)\b.*\b(spend|spending|report)\b',
            r'\b(create|generate|build|make)\b.*\b.*\b(report|summary|dashboard|chart|graph)\b'
        ]
        
        # Upload intent patterns - file management, metadata updates
        upload_patterns = [
            r'\b(upload|add|import|load|file|document|excel|xlsx)\b',
            r'\b(describe|label|tag|categorize|classify|identify)\b.*\b(file|document|data)\b',
            r'\b(what is|what does|explain|tell me about)\b.*\b(this file|this document|this data)\b',
            r'\b(what is)\b.*\b(file|document)\b',
            r'\b(what is this)\b.*\b(file|document)\b',
            r'\b(please describe|please categorize|please identify)\b.*\b(file|document)\b',
            r'\b(metadata|information|details|description|notes|comments)\b'
        ]
        
        # Memory intent patterns - retrieving saved queries/reports
        memory_patterns = [
            r'\b(saved|previous|past|earlier|before|last|recent)\b.*\b(query|report|search|analysis)\b',
            r'\b(show|list|find|get|retrieve)\b.*\b(saved|previous|past)\b',
            r'\b(run|execute|repeat|redo)\b.*\b(query|report|analysis)\b',
            r'\b(history|log|record|track)\b.*\b(queries|reports|searches)\b',
            r'\b(show|list|find|get)\b.*\b(saved queries|saved reports|queries from|reports from)\b',
            r'\b(show me|show|list|find|get)\b.*\b(saved queries|saved reports)\b',
            r'\b(queries|reports)\b.*\b(from|of|in)\b.*\b(last|previous|past|week|month|day)\b'
        ]
        
        # Check for query intent
        for pattern in query_patterns:
            if re.search(pattern, text):
                logger.info(f"Detected query intent from pattern: {pattern}")
                return "query"
        
        # Check for report intent
        for pattern in report_patterns:
            if re.search(pattern, text):
                logger.info(f"Detected report intent from pattern: {pattern}")
                return "report"
        
        # Check for upload intent
        for pattern in upload_patterns:
            if re.search(pattern, text):
                logger.info(f"Detected upload intent from pattern: {pattern}")
                return "upload"
        
        # Check for memory intent
        for pattern in memory_patterns:
            if re.search(pattern, text):
                logger.info(f"Detected memory intent from pattern: {pattern}")
                return "memory"
        
        # Check context clues
        if context.get("has_saved_queries", False) and any(word in text for word in ["previous", "saved", "last", "before"]):
            return "memory"
        
        if context.get("has_saved_reports", False) and any(word in text for word in ["report", "summary", "dashboard"]):
            return "report"
        
        # Default to query if unclear
        logger.info("Intent unclear, defaulting to query")
        return "query"
        
    except Exception as e:
        logger.error(f"Error analyzing intent: {e}")
        return "query"  # Safe fallback

def route_by_explicit_intent(intent: str) -> str:
    """
    Route based on explicit intent provided in input
    
    Args:
        intent (str): Explicit intent from user input
        
    Returns:
        str: Agent name to route to
    """
    intent_mapping = {
        "query": "QueryAgent",
        "question": "QueryAgent", 
        "ask": "QueryAgent",
        "search": "QueryAgent",
        "find": "QueryAgent",
        "report": "ReportAgent",
        "summary": "ReportAgent",
        "dashboard": "ReportAgent",
        "chart": "ReportAgent",
        "upload": "UploadAgent",
        "file": "UploadAgent",
        "document": "UploadAgent",
        "memory": "MemoryAgent",
        "saved": "MemoryAgent",
        "previous": "MemoryAgent",
        "history": "MemoryAgent"
    }
    
    return intent_mapping.get(intent, "QueryAgent")

def route_by_detected_intent(intent: str, query_text: str, context: Dict[str, Any]) -> str:
    """
    Route based on detected intent from analysis
    
    Args:
        intent (str): Detected intent from analyze_intent()
        query_text (str): Original query text
        context (Dict[str, Any]): Context information
        
    Returns:
        str: Agent name to route to
    """
    # Map detected intents to agents
    intent_to_agent = {
        "query": "QueryAgent",
        "report": "ReportAgent", 
        "upload": "UploadAgent",
        "memory": "MemoryAgent",
        "unclear": "QueryAgent"  # Default fallback
    }
    
    agent_name = intent_to_agent.get(intent, "QueryAgent")
    
    # Additional context-based routing logic
    if intent == "query" and context.get("prefers_reports", False):
        # If user typically prefers reports, route to ReportAgent
        if any(word in query_text for word in ["summary", "overview", "breakdown"]):
            agent_name = "ReportAgent"
    
    return agent_name

def validate_agent_input(agent_input: Dict[str, Any]) -> bool:
    """
    Validate agent input dictionary
    
    Ensures the input contains required fields and has valid structure.
    
    Args:
        agent_input (Dict[str, Any]): Input to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check if input is a dictionary
        if not isinstance(agent_input, dict):
            logger.error("Agent input must be a dictionary")
            return False
        
        # Check for required fields
        required_fields = ["query_text"]
        for field in required_fields:
            if field not in agent_input:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate query_text
        query_text = agent_input.get("query_text", "")
        if not isinstance(query_text, str) or not query_text.strip():
            logger.error("query_text must be a non-empty string")
            return False
        
        # Validate optional fields if present
        if "doc_id" in agent_input:
            doc_id = agent_input["doc_id"]
            if not isinstance(doc_id, str) or not doc_id.strip():
                logger.error("doc_id must be a non-empty string if provided")
                return False
        
        if "context" in agent_input:
            context = agent_input["context"]
            if not isinstance(context, dict):
                logger.error("context must be a dictionary if provided")
                return False
        
        logger.info("Agent input validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Error validating agent input: {e}")
        return False

def get_routing_confidence(agent_input: Dict[str, Any]) -> float:
    """
    Get confidence score for routing decision
    
    Returns a confidence score (0.0 to 1.0) indicating how certain
    the routing decision is.
    
    Args:
        agent_input (Dict[str, Any]): Agent input dictionary
        
    Returns:
        float: Confidence score between 0.0 and 1.0
    """
    try:
        query_text = agent_input.get("query_text", "").lower()
        intent = agent_input.get("intent", "").lower()
        
        # High confidence if explicit intent provided
        if intent and intent in ["query", "report", "upload", "memory"]:
            return 0.9
        
        # Medium confidence for clear patterns
        clear_patterns = [
            r'\b(how much|how many|what|show me)\b',  # Query patterns
            r'\b(report|summary|dashboard|chart)\b',  # Report patterns
            r'\b(upload|add|import|file)\b',          # Upload patterns
            r'\b(saved|previous|past|history)\b'      # Memory patterns
        ]
        
        for pattern in clear_patterns:
            if re.search(pattern, query_text):
                return 0.8
        
        # Lower confidence for ambiguous cases
        return 0.6
        
    except Exception as e:
        logger.error(f"Error calculating routing confidence: {e}")
        return 0.5

def get_available_agents() -> List[str]:
    """
    Get list of available agents for routing
    
    Returns:
        List[str]: List of available agent names
    """
    return ["QueryAgent", "ReportAgent", "UploadAgent", "MemoryAgent"]

def log_routing_decision(agent_input: Dict[str, Any], selected_agent: str, confidence: float):
    """
    Log routing decision for debugging and analysis
    
    Args:
        agent_input (Dict[str, Any]): Original input
        selected_agent (str): Selected agent
        confidence (float): Routing confidence score
    """
    try:
        query_text = agent_input.get("query_text", "")[:100]  # Truncate for logging
        doc_id = agent_input.get("doc_id", "unknown")
        
        logger.info(f"Routing Decision - Doc: {doc_id}, Agent: {selected_agent}, "
                   f"Confidence: {confidence:.2f}, Query: '{query_text}...'")
        
    except Exception as e:
        logger.error(f"Error logging routing decision: {e}")
