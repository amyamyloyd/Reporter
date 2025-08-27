"""
AutoGen File Analyzer Agent for Excel file analysis
Phase 2A: File Upload & Analysis
Compatible with pyautogen 0.4.0 and openai 1.55.3
"""
import os
import json
import logging
from typing import Dict, Any, List

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import AutoGen components - pyautogen 0.1.14 structure
try:
    from autogen import AssistantAgent, UserProxyAgent
except ImportError as e:
    logger.error(f"Failed to import AutoGen components: {e}")
    raise

def create_file_analyzer():
    """
    Create AutoGen agent for analyzing one Excel file at a time
    Compatible with pyautogen 0.1.14
    
    Returns:
        AssistantAgent: Configured agent for file analysis
    """
    # AutoGen 0.4.0 syntax: modern config structure
    config_list = [{
        "model": "gpt-4o",  # Use GPT-4o for better performance
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "timeout": 120  # Increase timeout for complex analysis
    }]
    
    # Clear system message for file analysis
    system_message = """You are an Excel field extractor. Your job is simple:

EXTRACT FIELDS ONLY:
1. List the fields provided to you
2. Note any obvious patterns (dates, numbers, text)
3. Output minimal JSON with field names and basic types

OUTPUT FORMAT:
{
  "fields_extracted": ["Field1", "Field2", "Field3"],
  "field_count": 3,
  "notes": "Brief observation about field types"
}

RULES:
- NO deep analysis
- NO role assignments
- NO descriptions
- Just list fields and count them
- Keep response under 100 words
- Output ONLY the JSON"""

    try:
        # pyautogen 0.1.14 syntax: simpler agent creation
        agent = AssistantAgent(
            name="FileAnalyzer",
            llm_config={"config_list": config_list},
            system_message=system_message
        )
        logger.info("File analyzer agent created successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to create file analyzer agent: {e}")
        raise

def create_user_proxy():
    """
    Create user proxy for automated conversations
    Compatible with pyautogen 0.1.14
    
    Returns:
        UserProxyAgent: Configured user proxy
    """
    try:
        user_proxy = UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5,
            code_execution_config=False  # Disable code execution for this POC
        )
        logger.info("User proxy agent created successfully")
        return user_proxy
    except Exception as e:
        logger.error(f"Failed to create user proxy: {e}")
        raise

async def analyze_single_file(file_metadata: Dict[str, Any], user_input: str) -> Dict[str, Any]:
    """
    Analyze a single Excel file using AutoGen agents
    Compatible with pyautogen 0.1.14
    
    Args:
        file_metadata: File information including filename and fields
        user_input: User's description of the file
        
    Returns:
        Dict with analysis results or error information
    """
    try:
        # Create fresh agents for this analysis session (no shared state)
        analyzer = create_file_analyzer()
        user_proxy = create_user_proxy()
        
        # Clear any previous conversation state
        analyzer.reset()
        user_proxy.reset()
        
        # Build conversation starter with context
        conversation_starter = f"""
        Extract fields from this Excel file:

        File: {file_metadata.get('filename', 'Unknown')}
        Fields found: {', '.join(file_metadata.get('fields', []))}
        
        List the fields and output JSON format.
        """
        
        # Debug: Log what we're sending to the agent
        logger.info(f"=== DEBUG: Agent conversation starter ===")
        logger.info(f"File: {file_metadata.get('filename', 'Unknown')}")
        logger.info(f"Fields: {file_metadata.get('fields', [])}")
        logger.info(f"User input: {user_input}")
        logger.info(f"Conversation starter: {conversation_starter}")
        
        # Initiate chat - only 1 turn to get analysis and stop
        user_proxy.initiate_chat(
            analyzer,
            message=conversation_starter,
            max_turns=1
        )
        
        # Extract the last message from the analyzer
        # AutoGen 0.4.0: Check both possible message locations using objects, not names
        messages = None
        message_source = None
        
        if analyzer in user_proxy.chat_messages:
            messages = user_proxy.chat_messages[analyzer]
            message_source = f"user_proxy.chat_messages[analyzer]"
        elif user_proxy in analyzer.chat_messages:
            messages = analyzer.chat_messages[user_proxy]
            message_source = f"analyzer.chat_messages[user_proxy]"
        
        if messages:
            logger.info(f"Found messages in {message_source}, count: {len(messages)}")
            last_message = messages[-1]["content"]
            logger.info(f"Agent response received: {last_message[:200]}...")
        else:
            # Debug: Log what we found in both locations
            logger.error(f"No messages found in either location")
            logger.error(f"user_proxy.chat_messages keys: {list(user_proxy.chat_messages.keys())}")
            logger.error(f"analyzer.chat_messages keys: {list(analyzer.chat_messages.keys())}")
            return {
                "success": False,
                "error": "No response from analyzer agent"
            }
            
        # Try to parse JSON response
        try:
            analysis_result = json.loads(last_message)
            return {
                "success": True, 
                "analysis": analysis_result,
                "raw_response": last_message
            }
        except json.JSONDecodeError:
            # Return structured response even if JSON parsing fails
            return {
                "success": True,
                "analysis": {
                    "file_purpose": "Analysis completed",
                    "fields": {},
                    "raw_response": last_message
                },
                "raw_response": last_message
            }
            
    except Exception as e:
        logger.error(f"File analysis failed: {e}")
        return {
            "success": False, 
            "error": f"Agent conversation failed: {str(e)}"
        }
