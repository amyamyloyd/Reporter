#!/usr/bin/env python3
"""
Test is_data_query function logic directly
Copy the function logic to test it independently
"""

import re

def is_simple_document_type(user_input: str) -> bool:
    """Check if user input is a simple, clear document type name"""
    if not user_input or not user_input.strip():
        return False
    
    words = user_input.strip().split()
    
    # Check for simple patterns: 1-2 words, reasonable length
    if len(words) <= 2 and len(user_input.strip()) < 50:
        # Additional check: not vague responses
        vague_responses = ["i don't know", "not sure", "whatever", "i don't care", "whatever you want"]
        if user_input.lower().strip() not in vague_responses:
            return True
    
    return False

def is_data_query(user_input: str) -> bool:
    """Detect if user is asking a data question instead of answering classification"""
    if not user_input or not user_input.strip():
        return False
    
    # Convert to lowercase for pattern matching
    input_lower = user_input.lower().strip()
    
    # Define query intent patterns
    query_patterns = [
        r'what.*(hotels?|data|records?|information|items?|entries?)',
        r'how many.*(hotels?|records?|items?|entries?|data)',
        r'show me.*(hotels?|data|records?|information)',
        r'list.*(hotels?|data|records?|information)',
        r'find.*(hotels?|data|records?|information)',
        r'query.*(hotels?|data|records?|information)',
        r'display.*(hotels?|data|records?|information)',
        r'get.*(hotels?|data|records?|information)',
        r'count.*(hotels?|records?|items?|entries?)',
        r'search.*(hotels?|data|records?|information)',
        r'filter.*(hotels?|data|records?|information)',
        r'sort.*(hotels?|data|records?|information)',
        r'group.*(hotels?|data|records?|information)',
        r'summarize.*(hotels?|data|records?|information)',
        r'analyze.*(hotels?|data|records?|information)'
    ]
    
    # Check if input matches any query pattern
    print(f"🔍 Debug: Testing patterns against: '{input_lower}'")
    for i, pattern in enumerate(query_patterns):
        match = re.search(pattern, input_lower)
        print(f"🔍 Debug: Pattern {i+1}: {pattern} -> {bool(match)}")
        if match:
            print(f"🔍 Debug: MATCH FOUND with pattern: {pattern}")
            return True
    
    # Additional checks for common query words
    query_words = ['what', 'how many', 'show', 'list', 'find', 'query', 'display', 'get', 'count', 'search', 'filter', 'sort', 'group', 'summarize', 'analyze']
    print(f"🔍 Debug: Checking query words: {query_words}")
    found_query_words = [word for word in query_words if word in input_lower]
    print(f"🔍 Debug: Found query words: {found_query_words}")
    
    if found_query_words:
        # Check if it's not just a simple document type name
        is_simple = is_simple_document_type(user_input)
        print(f"🔍 Debug: Is simple document type: {is_simple}")
        if not is_simple:
            print(f"🔍 Debug: Query words found and not simple -> TRUE")
            return True
        else:
            print(f"🔍 Debug: Query words found but simple document type -> FALSE")
    else:
        print(f"🔍 Debug: No query words found -> FALSE")
    
    return False

def test_is_data_query_simple():
    """Test the is_data_query function logic"""
    print("🚀 Testing is_data_query function logic")
    print("=" * 50)
    
    test_cases = [
        "how many hotels are in chicago?",
        "what hotels are in chicago?", 
        "show me the data",
        "list all hotels",
        "Locations",
        "Hotels",
        "find hotels in chicago",
        "count the records"
    ]
    
    for test_input in test_cases:
        print(f"\n--- Testing: '{test_input}' ---")
        result = is_data_query(test_input)
        print(f"Final Result: {result}")
        print("-" * 30)

if __name__ == "__main__":
    test_is_data_query_simple()
