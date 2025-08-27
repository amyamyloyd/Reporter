"""
AutoGen File Analyzer Agent for Excel file analysis
Phase 2A: File Upload & Analysis
Compatible with pyautogen 0.1.14
"""
import os
from typing import Dict, Any, List
from autogen import AssistantAgent, UserProxyAgent
import logging

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_file_analyzer():
    """
    Create AutoGen agent for analyzing one Excel file at a time
    Compatible with pyautogen 0.1.14
    
    Returns:
        AssistantAgent: Configured agent for file analysis
    """
    # pyautogen 0.1.14 syntax: simpler config structure
    config_list = [{
        "model": "gpt-4",
        "api_key": os.environ.get("OPENAI_API_KEY")
    }]
    
    # Clear system message for file analysis
    system_message = """You are an Excel data analysis specialist. Your job:

1. Analyze ONE Excel file at a time
2. Ask user what the file represents (e.g., "inventory data", "sales records")  
3. Identify key reporting fields (metrics like Cost, Quantity, Revenue)
4. Identify join fields that link to other files (like Company Code, Product ID)
5. Output structured JSON with field roles

Be conversational but focused. Guide non-technical users through data modeling.

Example output format:
{
  "file_purpose": "Monthly inventory tracking",
  "fields": {
    "Company Code": {"type": "string", "role": "join_field"},
    "Product Cost": {"type": "float", "role": "reporting_field"},  
    "Quantity": {"type": "integer", "role": "reporting_field"}
  }
}

Keep responses concise and helpful."""

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
            max_consecutive_auto_reply=5
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
        # Create agents for this analysis session
        analyzer = create_file_analyzer()
        user_proxy = create_user_proxy()
        
        # Build conversation starter with context
        conversation_starter = f"""
        File: {file_metadata.get('filename', 'Unknown')}
        Fields found: {', '.join(file_metadata.get('fields', []))}
        User description: {user_input}
        
        Please analyze this file and identify field roles.
        """
        
        # Initiate chat
        user_proxy.initiate_chat(
            analyzer,
            message=conversation_starter,
            max_turns=3
        )
        
        # Extract the last response from the analyzer
        if analyzer.chat_messages and user_proxy.name in analyzer.chat_messages:
            last_message = analyzer.chat_messages[user_proxy.name][-1]["content"]
        else:
            # Fallback: try to get from user proxy messages
            last_message = user_proxy.chat_messages[analyzer][-1]["content"]
        
        # Try to parse JSON response
        import json
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
