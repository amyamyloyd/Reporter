"""
Test ChatAgent - First Interface with User
AutoGen Excel Intelligence System - Phase 3

This test validates the ChatAgent functionality including:
- Agent creation and initialization
- Natural language input processing
- localStorage context injection
- Structured output generation
"""

import os
import json
import sys
import logging
from typing import Dict, Any

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the ChatAgent
from agents.chat_agent import ChatAgent, create_chat_agent

# Configure logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chat_agent_creation():
    """
    Test ChatAgent creation and initialization
    """
    print("=== Testing ChatAgent Creation ===")
    
    try:
        # Test agent creation
        chat_agent = create_chat_agent("TestChatAgent")
        
        # Verify agent properties
        assert chat_agent.name == "TestChatAgent"
        assert chat_agent.llm_config is not None
        assert "config_list" in chat_agent.llm_config
        
        # Test agent info
        agent_info = chat_agent.get_agent_info()
        assert agent_info["name"] == "TestChatAgent"
        assert agent_info["type"] == "ConversableAgent"
        assert "capabilities" in agent_info
        
        print("✅ ChatAgent creation test PASSED")
        print(f"   Agent name: {chat_agent.name}")
        print(f"   Agent type: {agent_info['type']}")
        print(f"   Capabilities: {len(agent_info['capabilities'])}")
        
        return chat_agent
        
    except Exception as e:
        print(f"❌ ChatAgent creation test FAILED: {e}")
        raise

def test_chat_agent_input_processing():
    """
    Test ChatAgent natural language input processing
    """
    print("\n=== Testing ChatAgent Input Processing ===")
    
    try:
        # Create agent
        chat_agent = create_chat_agent("TestChatAgent")
        
        # Test cases with different types of input
        test_cases = [
            {
                "name": "Simple Query",
                "input": "How much did we spend on Vendor X in Q2?",
                "context": {
                    "doc_id": "hospital_ledger_fy2024_001",
                    "schema": ["Vendor", "Date", "Amount"],
                    "record_count": 1200,
                    "duckdb_table_name": "hospital_ledger_fy2024_001"
                }
            },
            {
                "name": "Report Request",
                "input": "Generate a weekly spending report",
                "context": {
                    "doc_id": "financial_data_2024",
                    "schema": ["Week", "Category", "Amount"],
                    "record_count": 500,
                    "duckdb_table_name": "financial_data_2024"
                }
            },
            {
                "name": "Memory Request",
                "input": "Show me my saved queries",
                "context": {
                    "doc_id": "projects_2024",
                    "schema": ["Project", "Status", "Budget"],
                    "record_count": 50,
                    "duckdb_table_name": "projects_2024"
                }
            },
            {
                "name": "Upload Request",
                "input": "This file contains employee data",
                "context": {
                    "doc_id": "",
                    "schema": [],
                    "record_count": 0,
                    "duckdb_table_name": ""
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n--- Testing: {test_case['name']} ---")
            
            # Process input
            result = chat_agent.process_user_input(
                test_case["input"], 
                test_case["context"]
            )
            
            # Validate result structure
            assert "doc_id" in result
            assert "query_text" in result
            assert "intent" in result
            assert "context" in result
            assert "datetime_context" in result
            
            # Validate specific fields
            assert result["query_text"] == test_case["input"]
            assert result["doc_id"] == test_case["context"]["doc_id"]
            assert isinstance(result["context"], dict)
            assert isinstance(result["datetime_context"], dict)
            
            # Validate context injection
            assert result["context"]["schema"] == test_case["context"]["schema"]
            assert result["context"]["record_count"] == test_case["context"]["record_count"]
            assert result["context"]["duckdb_table_name"] == test_case["context"]["duckdb_table_name"]
            
            # Validate datetime context
            assert "now" in result["datetime_context"]
            assert "current_quarter" in result["datetime_context"]
            assert "last_quarter" in result["datetime_context"]
            
            print(f"✅ {test_case['name']} test PASSED")
            print(f"   Input: {test_case['input'][:50]}...")
            print(f"   Doc ID: {result['doc_id']}")
            print(f"   Intent: {result['intent']}")
            print(f"   Schema fields: {len(result['context']['schema'])}")
        
        print("\n✅ All input processing tests PASSED")
        
    except Exception as e:
        print(f"❌ Input processing test FAILED: {e}")
        raise

def test_chat_agent_error_handling():
    """
    Test ChatAgent error handling with invalid inputs
    """
    print("\n=== Testing ChatAgent Error Handling ===")
    
    try:
        # Create agent
        chat_agent = create_chat_agent("TestChatAgent")
        
        # Test cases with error conditions
        error_test_cases = [
            {
                "name": "Empty Input",
                "input": "",
                "context": None
            },
            {
                "name": "None Input",
                "input": None,
                "context": {}
            },
            {
                "name": "Invalid Context",
                "input": "Test query",
                "context": "invalid_context"
            }
        ]
        
        for test_case in error_test_cases:
            print(f"\n--- Testing Error Case: {test_case['name']} ---")
            
            try:
                # Process input (should handle errors gracefully)
                result = chat_agent.process_user_input(
                    test_case["input"], 
                    test_case["context"]
                )
                
                # Should still return valid structure
                assert "doc_id" in result
                assert "query_text" in result
                assert "intent" in result
                assert "context" in result
                assert "datetime_context" in result
                
                print(f"✅ {test_case['name']} error handling PASSED")
                print(f"   Result structure valid: {len(result)} fields")
                
            except Exception as e:
                print(f"❌ {test_case['name']} error handling FAILED: {e}")
                raise
        
        print("\n✅ All error handling tests PASSED")
        
    except Exception as e:
        print(f"❌ Error handling test FAILED: {e}")
        raise

def test_chat_agent_quarter_calculation():
    """
    Test ChatAgent quarter calculation functionality
    """
    print("\n=== Testing ChatAgent Quarter Calculation ===")
    
    try:
        # Create agent
        chat_agent = create_chat_agent("TestChatAgent")
        
        # Test quarter calculation methods
        current_quarter = chat_agent._get_current_quarter()
        last_quarter = chat_agent._get_last_quarter()
        
        # Validate quarter format
        assert current_quarter in ["Q1", "Q2", "Q3", "Q4"]
        assert last_quarter in ["Q1", "Q2", "Q3", "Q4"]
        
        # Validate quarter logic
        quarter_map = {"Q1": "Q4", "Q2": "Q1", "Q3": "Q2", "Q4": "Q3"}
        expected_last = quarter_map.get(current_quarter)
        assert last_quarter == expected_last
        
        print("✅ Quarter calculation test PASSED")
        print(f"   Current quarter: {current_quarter}")
        print(f"   Last quarter: {last_quarter}")
        
    except Exception as e:
        print(f"❌ Quarter calculation test FAILED: {e}")
        raise

def run_comprehensive_chat_agent_test():
    """
    Run comprehensive ChatAgent test suite
    """
    print("🧠 ChatAgent Comprehensive Test Suite")
    print("=" * 50)
    
    try:
        # Test 1: Agent Creation
        chat_agent = test_chat_agent_creation()
        
        # Test 2: Input Processing
        test_chat_agent_input_processing()
        
        # Test 3: Error Handling
        test_chat_agent_error_handling()
        
        # Test 4: Quarter Calculation
        test_chat_agent_quarter_calculation()
        
        print("\n" + "=" * 50)
        print("🎉 ALL CHATAGENT TESTS PASSED!")
        print("✅ ChatAgent is ready for integration")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"❌ CHATAGENT TESTS FAILED: {e}")
        print("=" * 50)
        return False

if __name__ == "__main__":
    # Run the comprehensive test
    success = run_comprehensive_chat_agent_test()
    
    if success:
        print("\n🚀 ChatAgent is ready for the next phase!")
        print("   Next: Test OrchestrationAgent")
    else:
        print("\n🔧 ChatAgent needs fixes before proceeding")
        sys.exit(1)
