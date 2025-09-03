# Bug List - AutoGen Excel Intelligence System

## Document Classification and Registry Issues

### Issue #1: Document Type Classification Not Working
**Status**: Open  
**Priority**: High  
**Component**: AgentChat.js, /chat-agent endpoint, Document Registry

**Description**: 
User uploaded `Vendors.xlsx` - this document type is not in the `doc_registry` in DuckDB. The document was processed (JSON file created, DuckDB table created) but `"ready_for_sql_agent": false`. 

**Expected Behavior**:
1. When document type is not in `doc_registry`, the agent should:
   - List the fields found in the document
   - Ask user to confirm the fields are correct
   - Ask user "What type of document is this?" 
   - User responds (e.g., "we track our vendors")
   - Agent gets document name and code from user response
   - Store new document type to `doc_registry` in DuckDB
   - Set/increment version in JSON if this is a new version of existing doc type
   - Set `ready_for_sql_agent: true`

**Current Behavior**:
- Document processed but `ready_for_sql_agent: false`
- No conversation initiated to classify document type
- Document type not added to `doc_registry`

**Use Case**:
User has a document type "Company Financial Report" that they upload weekly. The queries for this doc type (and reports in future) should be preloaded and available.

**Files Affected**:
- `frontend/src/components/AgentChat.js` - Not initiating classification conversation
- `backend/app.py` - `/chat-agent` endpoint not handling unknown document types
- `backend/agents/` - Agents not following document classification patterns

**Questions**:
1. Are we still using the `ready_for_sql_agent` flag?
2. Should we review the old agent patterns for document classification?
3. Is the document classification flow implemented in the new AutoGen agents?

**Next Steps**:
- Review old agent patterns for document classification
- Implement proper document type detection and classification flow
- Ensure new document types are added to `doc_registry`
- Test with unknown document types

---

### Issue #2: AutoGen Agent Conversation Abruptly Ends
**Status**: Open  
**Priority**: High  
**Component**: AutoGen Agent System, QueryAgent

**Description**: 
User uploads a document and asks "how many vendors are in chicago and boston?" The conversation shows "AutoGen agent processing completed" but no answer is provided and the conversation abruptly ends.

**Expected Behavior**:
1. User asks query about uploaded data
2. AutoGen agent processes the query
3. Agent generates SQL query
4. Agent executes query via DuckDB
5. Agent returns results with summary
6. Conversation continues with results displayed

**Current Behavior**:
- Query submitted successfully
- "AutoGen agent processing completed" message appears
- No results returned
- Conversation ends abruptly
- No error message shown

**Files Affected**:
- `backend/agents/query_agent.py` - QueryAgent processing
- `backend/agents/agent_orchestrator.py` - Agent orchestration
- `frontend/src/components/AutoGenChat.js` - Frontend conversation handling

**Possible Causes**:
1. QueryAgent SQL generation failing
2. DuckDB execution error
3. Agent conversation termination condition triggered
4. Frontend not handling agent response properly
5. LLM fallback not working for location-based queries

**Next Steps**:
- Debug QueryAgent processing for location-based queries
- Check DuckDB table creation and data availability
- Verify agent conversation flow and termination conditions
- Test with simpler queries first
