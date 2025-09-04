#!/usr/bin/env python3
"""
Phase 2 Integration Test - ChatAgent Classification
AutoGen Excel Intelligence System - Classification Enhancement

This script tests the Phase 2 integration of classification capabilities
into the ChatAgent and upload flow.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chat_agent_classification():
    """Test ChatAgent classification capabilities"""
    try:
        print("=== Testing ChatAgent Classification Integration ===")
        
        # Set mock API key for testing
        os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
        
        # Import ChatAgent
        from agents.chat_agent import create_chat_agent
        
        # Create ChatAgent instance
        chat_agent = create_chat_agent("TestChatAgent")
        print("✅ ChatAgent created successfully")
        
        # Test classification intent detection
        test_inputs = [
            "What type of document is this?",
            "Yes, that's correct",
            "Show me my document types",
            "Rename this to 'Financial Report'",
            "This should be classified as 'Budget Data'"
        ]
        
        for user_input in test_inputs:
            intent = chat_agent._detect_classification_intent(user_input)
            print(f"Input: '{user_input}' -> Intent: {intent}")
        
        # Test suggest_document_type with sample context
        sample_context = {
            "doc_id": "test_doc_001",
            "fields": ["Invoice_Number", "Date", "Amount", "Customer_Name"],
            "metadata": {
                "filename": "test_invoice.xlsx",
                "file_size": 1024,
                "record_count": 100
            }
        }
        
        print("\n--- Testing suggest_document_type ---")
        suggestion_response = chat_agent.suggest_document_type(sample_context)
        print(f"Suggestion Response: {json.dumps(suggestion_response, indent=2)}")
        
        # Test list_known_types
        print("\n--- Testing list_known_types ---")
        list_response = chat_agent.list_known_types()
        print(f"List Response: {json.dumps(list_response, indent=2)}")
        
        print("\n✅ ChatAgent classification tests completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ ChatAgent classification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase1_components():
    """Test Phase 1 components integration"""
    try:
        print("\n=== Testing Phase 1 Components Integration ===")
        
        # Test question generator
        from utils.classification_questions import create_question_generator, QuestionType
        
        generator = create_question_generator()
        print("✅ Question generator created successfully")
        
        # Test question generation
        match_question = generator.get_question(
            QuestionType.DOCUMENT_TYPE_MATCH_FOUND,
            {"doc_type": "Financial Report"}
        )
        print(f"Match Question: {match_question}")
        
        no_match_question = generator.get_question(QuestionType.NO_MATCH_FOUND)
        print(f"No Match Question: {no_match_question}")
        
        # Test fuzzy matcher
        from utils.fuzzy_classification import create_fuzzy_matcher
        
        matcher = create_fuzzy_matcher()
        print("✅ Fuzzy matcher created successfully")
        
        # Test field normalization
        test_fields = ["Invoice_Number", "Date", "Amount"]
        normalized = [matcher._normalize_field_name(field) for field in test_fields]
        print(f"Field normalization: {test_fields} -> {normalized}")
        
        # Test classification utils
        from utils.classification_utils import create_classification_utils
        
        utils = create_classification_utils()
        print("✅ Classification utils created successfully")
        
        # Test field analysis
        analysis = utils._analyze_fields(test_fields)
        print(f"Field analysis: {analysis}")
        
        print("\n✅ Phase 1 components integration tests completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Phase 1 components test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_upload_flow_integration():
    """Test upload flow integration (simulated)"""
    try:
        print("\n=== Testing Upload Flow Integration ===")
        
        # Set mock API key for testing
        os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
        
        # Test that we can import the modified app.py components
        from agents.chat_agent import create_chat_agent
        from utils.fuzzy_classification import create_fuzzy_matcher
        
        # Simulate upload flow classification logic
        sample_fields = ["Company", "Revenue", "Date", "Department"]
        
        # Test fuzzy matching (simulated)
        matcher = create_fuzzy_matcher()
        print("✅ Fuzzy matcher ready for upload flow")
        
        # Test ChatAgent classification (simulated)
        chat_agent = create_chat_agent()
        print("✅ ChatAgent ready for upload flow")
        
        # Test classification context preparation
        classification_context = {
            "doc_id": "test_upload_001",
            "fields": sample_fields,
            "metadata": {
                "filename": "test_upload.xlsx",
                "file_size": 2048,
                "record_count": 50
            }
        }
        
        # Test suggestion generation
        suggestion = chat_agent.suggest_document_type(classification_context)
        print(f"Upload flow classification suggestion: {suggestion.get('message', 'No message')}")
        
        print("\n✅ Upload flow integration tests completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Upload flow integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Phase 2 integration tests"""
    print("🚀 Starting Phase 2 Integration Tests")
    print("=" * 50)
    
    test_results = []
    
    # Run tests
    test_results.append(("ChatAgent Classification", test_chat_agent_classification()))
    test_results.append(("Phase 1 Components", test_phase1_components()))
    test_results.append(("Upload Flow Integration", test_upload_flow_integration()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Phase 2 Integration Test Results")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 2 integration tests passed!")
        print("✅ Phase 2 implementation is ready for use")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
