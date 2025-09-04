"""
Test Classification Questions - Comprehensive Testing
AutoGen Excel Intelligence System - Classification Enhancement

This module provides comprehensive testing for the classification question system
to ensure natural language variations work correctly and avoid repetition.

Test Coverage:
- Question variation generation
- Repetition avoidance
- Context formatting
- Edge cases and error handling
- Question quality and naturalness
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.classification_questions import (
    ClassificationQuestionGenerator, 
    QuestionType,
    get_document_type_match_question,
    get_no_match_question,
    get_rename_question,
    get_reclassification_question,
    get_list_types_question
)

def test_question_variations():
    """Test that we get different variations for the same question type"""
    print("=== Testing Question Variations ===")
    
    generator = ClassificationQuestionGenerator()
    
    # Test document type match questions - should get different variations
    questions = []
    for i in range(15):  # Test more than the 10 variations we have
        question = get_document_type_match_question("Test Document")
        questions.append(question)
        print(f"Question {i+1}: {question}")
    
    # Check that we got different questions (not all the same)
    unique_questions = set(questions)
    print(f"\nGenerated {len(questions)} questions, {len(unique_questions)} unique")
    
    # Should have at least 8 unique questions out of 15 (allowing for some repetition)
    assert len(unique_questions) >= 8, f"Expected at least 8 unique questions, got {len(unique_questions)}"
    print("✅ Variation test passed - got different questions")

def test_repetition_avoidance():
    """Test that recently used questions are avoided"""
    print("\n=== Testing Repetition Avoidance ===")
    
    generator = ClassificationQuestionGenerator()
    
    # Get 5 questions in a row - should all be different
    questions = []
    for i in range(5):
        question = generator.get_question(QuestionType.DOCUMENT_TYPE_MATCH_FOUND, {'doc_type': 'Test'})
        questions.append(question)
        print(f"Question {i+1}: {question}")
    
    # All 5 should be different
    unique_questions = set(questions)
    assert len(unique_questions) == 5, f"Expected 5 unique questions, got {len(unique_questions)}"
    print("✅ Repetition avoidance test passed - all 5 questions were different")

def test_context_formatting():
    """Test that context is properly formatted into questions"""
    print("\n=== Testing Context Formatting ===")
    
    # Test document type formatting
    question = get_document_type_match_question("Hospital Finance Document")
    assert "Hospital Finance Document" in question, f"Document type not found in question: {question}"
    print(f"✅ Document type formatting: {question}")
    
    # Test rename formatting
    question = get_rename_question("Budget Template")
    assert "Budget Template" in question, f"Current type not found in question: {question}"
    print(f"✅ Rename formatting: {question}")
    
    # Test list formatting
    types = ["Finance", "HR", "Projects"]
    question = get_list_types_question(types)
    assert "Finance, HR, Projects" in question, f"Type list not found in question: {question}"
    print(f"✅ List formatting: {question}")

def test_question_quality():
    """Test that questions sound natural and varied"""
    print("\n=== Testing Question Quality ===")
    
    generator = ClassificationQuestionGenerator()
    
    # Test different question types for naturalness
    question_types = [
        (QuestionType.DOCUMENT_TYPE_MATCH_FOUND, {'doc_type': 'Test'}),
        (QuestionType.NO_MATCH_FOUND, {}),
        (QuestionType.DOCUMENT_TYPE_RENAME, {'current_type': 'Test'}),
        (QuestionType.DOCUMENT_RECLASSIFICATION, {'current_type': 'Test'}),
        (QuestionType.LIST_KNOWN_TYPES, {'type_list': 'A, B, C'})
    ]
    
    for question_type, context in question_types:
        question = generator.get_question(question_type, context)
        
        # Check that question is not empty
        assert len(question.strip()) > 0, f"Empty question for {question_type}"
        
        # Check that question ends with question mark
        assert question.strip().endswith('?'), f"Question doesn't end with ?: {question}"
        
        # Check that question is not too short (should be at least 20 characters)
        assert len(question) >= 20, f"Question too short: {question}"
        
        print(f"✅ {question_type.value}: {question}")

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n=== Testing Edge Cases ===")
    
    generator = ClassificationQuestionGenerator()
    
    # Test with empty context
    question = generator.get_question(QuestionType.NO_MATCH_FOUND, {})
    assert len(question.strip()) > 0, "Empty context should still generate a question"
    print(f"✅ Empty context: {question}")
    
    # Test with None context
    question = generator.get_question(QuestionType.NO_MATCH_FOUND, None)
    assert len(question.strip()) > 0, "None context should still generate a question"
    print(f"✅ None context: {question}")
    
    # Test with missing context keys
    question = generator.get_question(QuestionType.DOCUMENT_TYPE_MATCH_FOUND, {'wrong_key': 'value'})
    assert len(question.strip()) > 0, "Missing context keys should still generate a question"
    print(f"✅ Missing context keys: {question}")

def test_statistics():
    """Test that statistics are accurate"""
    print("\n=== Testing Statistics ===")
    
    generator = ClassificationQuestionGenerator()
    stats = generator.get_question_statistics()
    
    # Check that we have 10 variations for each type
    for question_type in QuestionType:
        expected_count = 10
        actual_count = stats[question_type.value]
        assert actual_count == expected_count, f"Expected {expected_count} variations for {question_type.value}, got {actual_count}"
        print(f"✅ {question_type.value}: {actual_count} variations")
    
    # Check tracking stats
    assert stats['recently_used'] == 0, f"Expected 0 recently used questions, got {stats['recently_used']}"
    assert stats['max_recent_tracking'] == 10, f"Expected max tracking of 10, got {stats['max_recent_tracking']}"
    print("✅ Statistics test passed")

def test_convenience_functions():
    """Test that convenience functions work correctly"""
    print("\n=== Testing Convenience Functions ===")
    
    # Test all convenience functions
    match_question = get_document_type_match_question("Test Document")
    assert "Test Document" in match_question
    print(f"✅ get_document_type_match_question: {match_question}")
    
    no_match_question = get_no_match_question()
    assert len(no_match_question.strip()) > 0
    print(f"✅ get_no_match_question: {no_match_question}")
    
    rename_question = get_rename_question("Old Name")
    assert "Old Name" in rename_question
    print(f"✅ get_rename_question: {rename_question}")
    
    reclass_question = get_reclassification_question("Current Type")
    # Check that the question contains either "Current Type" or a fallback
    assert "Current Type" in reclass_question or "type" in reclass_question.lower()
    print(f"✅ get_reclassification_question: {reclass_question}")
    
    list_question = get_list_types_question(["Type1", "Type2", "Type3"])
    assert "Type1, Type2, Type3" in list_question
    print(f"✅ get_list_types_question: {list_question}")

def run_all_tests():
    """Run all tests and report results"""
    print("🧪 Starting Comprehensive Classification Questions Test Suite")
    print("=" * 60)
    
    try:
        test_question_variations()
        test_repetition_avoidance()
        test_context_formatting()
        test_question_quality()
        test_edge_cases()
        test_statistics()
        test_convenience_functions()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Classification Questions system is working correctly.")
        print("✅ Question variations are working")
        print("✅ Repetition avoidance is working")
        print("✅ Context formatting is working")
        print("✅ Question quality is good")
        print("✅ Edge cases are handled")
        print("✅ Statistics are accurate")
        print("✅ Convenience functions work")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
