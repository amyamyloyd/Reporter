# tests/test_conversation_plumbing.py
"""
Phase 1 Tests - Conversation Plumbing
Tests for conversation_id generation and context management
"""
import types
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.chat_agent import create_chat_agent
from agents.query_agent import create_query_agent

def make_ctx(doc_id="doc123", table="tbl_hotels", conversation_id="conv-abc"):
    """Create test context with conversation_id"""
    return {
        "doc_id": doc_id,
        "schema": ["Hotel Name", "Location (city)", "Discount Rate"],
        "record_count": 1000,
        "duckdb_table_name": table,
        "metadata": {"duckdb_table_name": table, "fields": ["Hotel Name", "Location (city)", "Discount Rate"]},
        "conversation_id": conversation_id
    }

def test_chat_agent_includes_conversation_id():
    """Test that ChatAgent includes conversation_id in structured output"""
    agent = create_chat_agent("ChatAgentTest")
    ctx = make_ctx()
    out = agent.process_user_input("hello", ctx)
    assert out["context"]["conversation_id"] == "conv-abc"

def test_query_agent_context_key_uses_conversation_id(monkeypatch):
    """Test that QueryAgent uses (conversation_id, doc_id) as context key"""
    qa = create_query_agent("QueryAgentTest")
    structured = {
        "doc_id": "doc123",
        "query_text": "how many are in detroit?",
        "context": make_ctx(),
        "datetime_context": {"now": "2025-09-05T12:00:00"}
    }
    # Force _is_ambiguous_query to True so it stores context
    monkeypatch.setattr(qa, "_is_ambiguous_query", lambda q: True)
    res = qa.process_query_request(structured)
    assert res.get("clarification"), "Should request clarification and store context keyed by (conv, doc)"
    key = (structured["context"]["conversation_id"], structured["doc_id"])
    assert key in qa.query_context

def test_query_agent_context_key_isolation():
    """Test that different conversations have isolated context"""
    qa = create_query_agent("QueryAgentTest2")
    
    # First conversation
    structured1 = {
        "doc_id": "doc123",
        "query_text": "how many are in detroit?",
        "context": make_ctx(conversation_id="conv-abc"),
        "datetime_context": {"now": "2025-09-05T12:00:00"}
    }
    
    # Second conversation with different conversation_id
    structured2 = {
        "doc_id": "doc123",  # Same doc_id
        "query_text": "how many are in chicago?",
        "context": make_ctx(conversation_id="conv-xyz"),  # Different conversation_id
        "datetime_context": {"now": "2025-09-05T12:00:00"}
    }
    
    # Mock _is_ambiguous_query to return True for both
    def mock_ambiguous(query):
        return "how many" in query.lower()
    
    qa._is_ambiguous_query = mock_ambiguous
    
    # Process first query
    res1 = qa.process_query_request(structured1)
    assert res1.get("clarification")
    
    # Process second query
    res2 = qa.process_query_request(structured2)
    assert res2.get("clarification")
    
    # Check that both contexts are stored separately
    key1 = ("conv-abc", "doc123")
    key2 = ("conv-xyz", "doc123")
    
    assert key1 in qa.query_context
    assert key2 in qa.query_context
    assert qa.query_context[key1]["original_query"] == "how many are in detroit?"
    assert qa.query_context[key2]["original_query"] == "how many are in chicago?"

if __name__ == "__main__":
    # Run tests
    test_chat_agent_includes_conversation_id()
    print("✓ ChatAgent conversation_id test passed")
    
    # Note: monkeypatch tests need pytest to run properly
    print("✓ QueryAgent context key tests defined (run with pytest)")
