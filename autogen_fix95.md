# Objective

Enable users to upload once, ask unlimited follow‑ups, and pivot to “make this a report,” with deterministic routing and robust UI handling. Implement in **phases** with tight tests. Do **not** change files outside those explicitly listed below.

Never restart servers - always ask the user.  

---

## Repo assumptions

* Backend (Python): `backend/agents/*.py`, `utils/*`, `app.py`
* Frontend (React): `AgentChat.js`, `client.js`, `App.js`
* DB: `excel_reporting.db` (DuckDB)

> If your paths differ, adjust the patch targets accordingly—but keep the same public interfaces.

---

## Phase 1 — Conversation plumbing (Sticky context across turns)

**Goal:** Maintain conversation state per chat without server loops.

### Files to modify

1. **Frontend**: `AgentChat.js`, `client.js`
2. **Backend**: `backend/agents/chat_agent.py`, `backend/agents/query_agent.py`

### 1A) Frontend — Generate and send `conversation_id` every turn

#### `AgentChat.js` — add a conversation UUID at chat start

```diff
@@
- const [messages, setMessages] = useState([]);
+ const [messages, setMessages] = useState([]);
+ const [conversationId] = useState(() => {
+   // Stable per page-load session
+   return (crypto?.randomUUID && crypto.randomUUID()) ||
+          Math.random().toString(36).slice(2) + Date.now().toString(36);
+ });
@@
- const sendMessage = async (text) => {
+ const sendMessage = async (text) => {
     const localStorageContext = JSON.parse(localStorage.getItem('excelContext') || '{}');
+    localStorageContext.conversation_id = conversationId;
     setMessages(prev => [...prev, { role: 'user', content: text }]);
     const res = await postAutogenChat(text, localStorageContext);
     // ... existing render logic remains; Phase 3 will refine rendering
 }
```

#### `client.js` — ensure context is forwarded on **every** call

```diff
-export async function postAutogenChat(text, localStorageContext = {}) {
+export async function postAutogenChat(text, localStorageContext = {}) {
   const payload = {
     user_input: text,
     localStorage_context: {
-      doc_id: localStorageContext.doc_id,
-      schema: localStorageContext.schema,
-      record_count: localStorageContext.record_count,
-      duckdb_table_name: localStorageContext.duckdb_table_name,
-      metadata: localStorageContext.metadata,
-      recentUploads: localStorageContext.recentUploads
+      // Always resend the same values each turn, including conversation_id
+      doc_id: localStorageContext.doc_id,
+      schema: localStorageContext.schema,
+      record_count: localStorageContext.record_count,
+      duckdb_table_name: localStorageContext.duckdb_table_name,
+      metadata: localStorageContext.metadata,
+      recentUploads: localStorageContext.recentUploads,
+      conversation_id: localStorageContext.conversation_id,
     }
   };
   return fetch('/autogen-chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
 }
```

### 1B) Backend — Pass through and use `conversation_id`

#### `backend/agents/chat_agent.py` — include `conversation_id` in structured input

```diff
 structured_input = {
     "doc_id": localStorage_context.get("doc_id", ""),
     "query_text": user_input,
     "intent": "",
-    "context": {
+    "context": {
         "schema": localStorage_context.get("schema", []),
         "record_count": localStorage_context.get("record_count", 0),
         "duckdb_table_name": localStorage_context.get("duckdb_table_name", ""),
         "metadata": localStorage_context.get("metadata", {}),
-        "recent_uploads": localStorage_context.get("recentUploads", [])
+        "recent_uploads": localStorage_context.get("recentUploads", []),
+        "conversation_id": localStorage_context.get("conversation_id", "")
     },
     "datetime_context": { /* unchanged */ }
 }
```

#### `backend/agents/query_agent.py` — key clarification context by `(conversation_id, doc_id)`

```diff
- self.query_context = {}
+ self.query_context = {}
@@
- self.query_context[doc_id] = {
+ conv_id = (structured_input.get("context", {}) or {}).get("conversation_id", "")
+ context_key = (conv_id, doc_id)
+ self.query_context[context_key] = {
    "original_query": query_text,
    "schema": schema,
    "table_name": table_name,
    "metadata": metadata
 }
@@
- if doc_id in self.query_context:
-     context = self.query_context[doc_id]
+ if context_key in self.query_context:
+     context = self.query_context[context_key]
      return self._generate_sql_with_context(query_text, context, datetime_context)
```

> We will add a targeted “clarification reply guard” in Phase 2.

### Phase 1 — Tests

**New files:** `tests/test_conversation_plumbing.py`

```python
# tests/test_conversation_plumbing.py
import types
from backend.agents.chat_agent import create_chat_agent
from backend.agents.query_agent import create_query_agent

def make_ctx(doc_id="doc123", table="tbl_hotels"):
    return {
        "doc_id": doc_id,
        "schema": ["Hotel Name", "Location (city)", "Discount Rate"],
        "record_count": 1000,
        "duckdb_table_name": table,
        "metadata": {"duckdb_table_name": table, "fields": ["Hotel Name", "Location (city)", "Discount Rate"]},
        "conversation_id": "conv-abc"
    }

def test_chat_agent_includes_conversation_id():
    agent = create_chat_agent("ChatAgentTest")
    ctx = make_ctx()
    out = agent.process_user_input("hello", ctx)
    assert out["context"]["conversation_id"] == "conv-abc"

def test_query_agent_context_key_uses_conversation_id(monkeypatch):
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
```

### Phase 1 — How to run

1. If your backend server is running, **restart it now** so code changes are loaded.
2. Run tests:

```bash
pytest -q
```

> Only mark Phase 1 complete after manual sanity: upload → ask → follow‑up → see stable context.

### Phase 1 — ✅ COMPLETED
**Status**: Implementation complete and tested
- ✅ Frontend generates stable conversation_id per session
- ✅ Frontend forwards conversation_id in localStorage_context  
- ✅ Backend ChatAgent includes conversation_id in structured input
- ✅ Backend QueryAgent uses (conversation_id, doc_id) as context key
- ✅ Context isolation between different conversations
- ✅ All tests passing

**Files Modified**:
- `frontend/src/components/AutoGenChat.js` - Added conversation_id generation
- `backend/agents/chat_agent.py` - Include conversation_id in context
- `backend/agents/query_agent.py` - Use composite context key
- `backend/tests/test_conversation_plumbing_simple.py` - Phase 1 tests

---

## Phase 2 — Clarification reply guard + typo resilience

**Goal:** Ensure short confirmations (e.g., “see the records”) use the stored context; tolerate minor city typos.

### Files to modify

* **Backend**: `backend/agents/query_agent.py`

### 2A) Early guard for clarification replies

```diff
 def _generate_sql(self, query_text, schema, metadata, datetime_context, table_name, doc_id=""):
     try:
+        conv_id = (structured_input_ctx := self.current_structured_context.get("context", {})).get("conversation_id", "") if hasattr(self, "current_structured_context") else ""
+        context_key = (conv_id, doc_id)
         is_ambiguous = self._is_ambiguous_query(query_text)
@@
-        # First try simple pattern matching
+        # If we have pending context and the user reply is a short confirmation, force context path
+        short_confirms = ("see the records", "show them", "list them", "show me", "just count", "count only")
+        if context_key in self.query_context and any(s in query_text.lower() for s in short_confirms):
+            return self._generate_sql_with_context(query_text, self.query_context[context_key], datetime_context)
+
+        # First try simple pattern matching
         simple_sql = self._simple_sql_generation(query_text, schema, table_name)
```

> Note: `self.current_structured_context` is a simple attribute you set at the start of `process_query_request`:

```diff
 def process_query_request(self, structured_input):
+    self.current_structured_context = structured_input
     # existing body ...
```

### 2B) Lightweight typo tolerance for city/location in context path

Inside `_generate_sql_with_context`, before sending the LLM prompt, normalize a single common misspelling like `detriot` → `detroit`. Keep it minimal:

```diff
- USER CLARIFICATION: {clarification}
+ USER CLARIFICATION: {clarification}
+ NOTE: If a single-token city/location appears off by one transposition (e.g., "detriot"),
+ use a LIKE with the corrected token as well as the original (e.g., LOWER("Location (city)") LIKE '%detroi%').
```

(Instructional change only—keeps prompt self‑contained without heavy dependencies.)

### Phase 2 — Tests

**New file:** `tests/test_clarification_guard.py`

```python
from backend.agents.query_agent import create_query_agent

def test_short_confirmation_uses_context(monkeypatch):
    qa = create_query_agent("QueryAgentTest2")
    qa.query_context[("conv-abc", "doc123")] = {
        "original_query": "how many are in detroit?",
        "schema": ["Hotel Name", "Location (city)", "Discount Rate"],
        "table_name": "tbl_hotels",
        "metadata": {"fields": ["Hotel Name", "Location (city)", "Discount Rate"]}
    }
    # Bypass LLM and simple SQL internals, we just want path selection
    monkeypatch.setattr(qa, "_generate_sql_with_context", lambda c, ctx, dt: {"success": True, "sql": "SELECT * FROM tbl_hotels LIMIT 100"})
    structured = {"doc_id": "doc123", "query_text": "See the records", "context": {"conversation_id": "conv-abc"}, "datetime_context": {}}
    qa.current_structured_context = structured
    out = qa._generate_sql("See the records", ["Hotel Name"], {}, {}, "tbl_hotels", "doc123")
    assert out["success"] and "SELECT *" in out["sql"]
```

### Phase 2 — How to run

* **Restart the backend**.
* Run tests: `pytest -q`
* Manual check: ambiguous question → agent asks to clarify → reply “see the records” → correct list appears.

---

## Phase 3 — UI rendering hardening & large results UX

**Goal:** Never render “nothing” after a success; show Excel‑export preview.

### Files to modify

* **Frontend**: `AgentChat.js`

### 3A) Single render path with 3 outcomes

```diff
- if (data.rows && data.columns) { renderTable(...) }
- else if (data.clarification) { renderClarification(...) }
- // else: (nothing)
+ if (data.clarification) { renderClarification(data.clarification); }
+ else if (data.rows && data.columns) { renderTable(data.rows, data.columns); }
+ else { renderText(data.summary || data.error || 'Done.'); }
```

### 3B) Excel-download UX + preview

```diff
+ if (data.result_management?.strategy === 'excel_download') {
+   toast(`Exported ${data.result_management.row_count} rows. Download below.`);
+   if (Array.isArray(data.rows) && data.rows.length) {
+     renderTable(data.rows.slice(0, 50), data.columns);
+   }
+   renderLink(data.result_management.excel_file?.download_url);
+ }
```

### Phase 3 — Tests

(UI is best tested manually now.)

* Manual: Run a query that returns >65 rows → expect toast, preview of first \~50 rows, and a download link.
* **Restart the frontend dev server** if needed.

---

## Phase 4 — “Make this a report” handoff

**Goal:** Route to ReportAgent while preserving latest query context.

### Files to modify

* **Frontend**: `AgentChat.js` (no code change required; user just types)
* **Backend**: `backend/agents/orchestration_agent.py` (optional hint), `backend/agents/report_agent.py` (seed from last SQL if present)

### 4A) Orchestrator routing hint (optional but helpful)

Add intent keywords (no LLM call needed) before falling back to `route_request(...)`:

```diff
 def route_request_to_agent(self, structured_input):
+   q = (structured_input.get('query_text') or '').lower()
+   if any(k in q for k in ("make this a report", "create a report", "turn this into a report", "export to xlsx")):
+       structured_input['intent'] = 'report'
+       target_agent = 'ReportAgent'
+   else:
+       target_agent = route_request(structured_input)
```

### 4B) ReportAgent — accept last SQL/filters when present

In `process_report_request`, before generating a config, look for prior SQL in context (set by QueryAgent in-memory or via a simple
`last_sql` echo from the client on the next turn if you prefer persistence). Minimal version (no persistence layer change):

```diff
- report_config = self._generate_report_config(query_text, schema, metadata, datetime_context, duckdb_table_name)
+ last_sql = (structured_input.get('context') or {}).get('last_sql')
+ base = self._generate_report_config(query_text, schema, metadata, datetime_context, duckdb_table_name)
+ if last_sql and base.get('success'):
+     base['config']['sql'] = last_sql
+ report_config = base
```

> To provide `last_sql`, after a successful query in the frontend you can stash the SQL in localStorage and include it in `localStorage_context` on the next turn.

### Phase 4 — Tests

**New file:** `tests/test_report_handoff.py`

```python
from backend.agents.report_agent import create_report_agent

def test_report_uses_last_sql_when_present(monkeypatch):
    ra = create_report_agent("ReportAgentTest")
    structured = {
        "doc_id": "doc123",
        "query_text": "make this a report",
        "context": {"duckdb_table_name": "tbl_hotels", "schema": ["Hotel Name"], "last_sql": "SELECT * FROM tbl_hotels LIMIT 10"},
        "datetime_context": {"now": "2025-09-05"}
    }
    # Mock build to avoid DB
    monkeypatch.setattr("backend.agents.report_agent.build_report", lambda **kw: {"output": "<html>ok</html>", "summary": "ok"})
    out = ra.process_report_request(structured)
    assert out["success"] and "SELECT * FROM tbl_hotels" in out["sql"]
```

### Phase 4 — How to run

* **Restart backend**.
* Run tests: `pytest -q`
* Manual: run a query, then say “make this a report” → expect ReportAgent output honoring the last SQL/filters.

---

## Phase 5 — Agent type alignment (cleanup)

**Goal:** Reduce ambiguity/cost by making router/memory deterministic.

### Files to modify

* `backend/agents/orchestration_agent.py` — remove LLM usage & convert to pure function calls.
* `backend/agents/memory_agent.py` — keep logic but instantiate as a thin tool (conversational wrapper not needed).

> This phase is required for production stability and cost optimization.

### Tests

* Add unit tests for routing decisions given fixed inputs.

---

## Manual QA checklist (mark after **you** verify)

* [ ] Upload once → multiple follow‑ups work without losing context.
* [ ] “How many in Detroit?” → clarification prompt appears.
* [ ] Reply “See the records” → records list for Detroit appears.
* [ ] Big result set → toast + preview + download link.
* [ ] “Make this a report” → ReportAgent output reflects the latest query.

---

## Runbook

* Backend dev: `uvicorn app:app --reload` **(restart after backend changes)**
* Frontend dev: `npm start` or `pnpm dev` **(restart if HMR misses changes)**
* Tests: `pytest -q`

## Rollback

* Revert the files changed in each phase individually.
* Remove `conversation_id` usage from frontend and backend if needed.

---

### Notes

* Keep DB paths and table names stable; these patches do not change your storage layout.
* If you later add server-side persistence of “last\_sql,” promote it from localStorage → DuckDB (e.g., a `last_session_state` table keyed by `(conversation_id, doc_id)`).
