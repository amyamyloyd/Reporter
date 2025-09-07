# Cursor Fix Pack: Sticky Conversations & Report Handoff

**Goal**

* After a single upload, the user can ask unlimited follow‑ups and then say “make this a report” to route to ReportAgent and produce output.
* Keep the server one‑shot per request (no background loops). Persist conversation via IDs and consistent context.
* Ship in **phases**, with unit tests and manual checkpoints. Do **not** mark a phase complete until you’ve run the tests and manually verified the acceptance steps.

**Ground Rules**

* Only modify files explicitly named in each phase.
* Add new files only under `tests/` (backend) and `__init__.py` if needed for test packages.
* Ask the operator to **start/restart servers** whenever a phase requires running code.

---

## Phase 1 — Conversation Plumbing (enable unlimited follow‑ups)

**Objective:** Introduce a sticky `conversation_id` and **always** resend file context every turn.

### Backend changes

Files:

* `chat_agent.py`
* `query_agent.py`

#### 1A) `chat_agent.py` — carry `conversation_id`

* **Change** `process_user_input` to read `conversation_id` from `localStorage_context` and include it in the `structured_input` dict (new top‑level key: `conversation_id`).
* **Add** a fallback: if `conversation_id` is missing, set `conversation_id` to an empty string (do **not** generate it here; that’s the frontend’s job).

**Patch (targeted snippet):**

```python
# chat_agent.py (inside process_user_input)
structured_input = {
    "conversation_id": localStorage_context.get("conversation_id", ""),  # <— NEW
    "doc_id": localStorage_context.get("doc_id", ""),
    "query_text": user_input,
    "intent": "",
    "context": {
        "schema": localStorage_context.get("schema", []),
        "record_count": localStorage_context.get("record_count", 0),
        "duckdb_table_name": localStorage_context.get("duckdb_table_name", ""),
        "metadata": localStorage_context.get("metadata", {}),
        "recent_uploads": localStorage_context.get("recentUploads", [])
    },
    "datetime_context": {...}
}
```

#### 1B) `query_agent.py` — key follow‑up context by `(conversation_id, doc_id)`

* **Change** `self.query_context` to a dict keyed by a tuple `(conversation_id, doc_id)`.
* Everywhere `self.query_context[...]` is set or read, compute `ctx_key = (conversation_id, doc_id)` first.
* If `conversation_id` is empty, still compute the tuple `("", doc_id)`; this keeps behavior stable when frontend hasn’t been updated yet.

**Patch (targeted snippets):**

```python
# query_agent.py (class __init__)
self.query_context = {}  # unchanged declaration

# query_agent.py (inside process_query_request)
conversation_id = structured_input.get("conversation_id", "")
doc_id = structured_input.get("doc_id", "")
...
# pass conversation_id down to _generate_sql
sql_result = self._generate_sql(query_text, schema, metadata, datetime_context, duckdb_table_name, doc_id, conversation_id)
```

```python
# query_agent.py (signature change)
def _generate_sql(self, query_text, schema, metadata, datetime_context, table_name, doc_id="", conversation_id=""):
    ...
    if is_ambiguous:
        ctx_key = (conversation_id, doc_id)
        self.query_context[ctx_key] = {
            "original_query": query_text,
            "schema": schema,
            "table_name": table_name,
            "metadata": metadata
        }
        return {"success": True, "clarification": ...}
    ...
    # clarification follow‑up
    ctx_key = (conversation_id, doc_id)
    if ctx_key in self.query_context:
        context = self.query_context[ctx_key]
        return self._generate_sql_with_context(query_text, context, datetime_context)
```

> **Note:** Update all internal calls to `_generate_sql(...)` to pass `conversation_id` (only within `query_agent.py`). No other files change in this phase for the backend.

### Frontend changes

Files:

* `AgentChat.js`
* `client.js`

#### 1C) Generate and send `conversation_id` on every request

* On chat open/mount, if `localStorage.conversation_id` is missing, generate a UUID (or timestamp‑based string) and store it.
* **Always** include `conversation_id`, `doc_id`, `duckdb_table_name`, `schema`, `record_count`, `metadata` in the body you POST to `/autogen-chat`.

**Patch (conceptual):**

```javascript
// AgentChat.js (on component mount)
if (!localStorage.getItem('conversation_id')) {
  localStorage.setItem('conversation_id', crypto.randomUUID());
}

// client.js (request builder)
const payload = {
  user_input,
  localStorage_context: {
    conversation_id: localStorage.getItem('conversation_id'),
    doc_id: localStorage.getItem('doc_id'),
    duckdb_table_name: localStorage.getItem('duckdb_table_name'),
    schema: JSON.parse(localStorage.getItem('schema') || '[]'),
    record_count: Number(localStorage.getItem('record_count') || 0),
    metadata: JSON.parse(localStorage.getItem('metadata') || '{}'),
    recentUploads: JSON.parse(localStorage.getItem('recentUploads') || '[]')
  }
};
```

### Tests (backend)

Add files under `tests/`:

* `tests/test_chat_agent_context.py`
* `tests/test_query_agent_session.py`

**`tests/test_chat_agent_context.py`**

```python
import pytest
from chat_agent import create_chat_agent

def test_chat_agent_includes_conversation_id():
    agent = create_chat_agent("ChatAgent")
    ctx = {"conversation_id": "c1", "doc_id": "d1"}
    out = agent.process_user_input("hello", ctx)
    assert out["conversation_id"] == "c1"
    assert out["doc_id"] == "d1"
```

**`tests/test_query_agent_session.py`** (uses a stubbed metadata loader; if needed, monkeypatch `load_metadata` to return a minimal dict with `duckdb_table_name`)

```python
import pytest
from query_agent import create_query_agent

class DummyMeta:
    @staticmethod
    def load_metadata(doc_id):
        return {"fields": ["Location (city)", "Discount Rate"],
                "duckdb_table_name": "test_table",
                "record_count": 10}

def test_query_agent_keys_context_by_tuple(monkeypatch):
    agent = create_query_agent("QueryAgent")
    monkeypatch.setattr("query_agent.load_metadata", lambda d: DummyMeta.load_metadata(d))
    s1 = {"conversation_id": "c1", "doc_id": "d1", "query_text": "how many in detroit?",
          "context": {}, "datetime_context": {"now": "now"}}
    r1 = agent.process_query_request(s1)
    assert r1.get("clarification")  # ambiguity expected

    s2 = {"conversation_id": "c1", "doc_id": "d1", "query_text": "see the records",
          "context": {}, "datetime_context": {"now": "now"}}
    r2 = agent.process_query_request(s2)
    # Should attempt context-aware SQL rather than defaulting to simple/LLM branches
    assert r2.get("sql") is not None
```

### Run tests

1. **Start/restart the backend server if required for your environment**, then in a separate shell run:

```
pytest -q
```

2. Do **not** mark Phase 1 complete until both tests pass and you’ve manually verified:

   * Upload once → ask a question → follow up with “how many …” → answer “see the records”: records render.

---

## Phase 2 — Clarification Early‑Guard (fix “See the records”)

**Objective:** Ensure short confirmations use the saved context and can’t be misrouted.

### Backend change

File:

* `query_agent.py`

#### 2A) Add early‑guard for clarification replies

* Inside `_generate_sql(...)`, **before** deciding simple vs LLM, detect if the user’s current text is a short confirm and `(conversation_id, doc_id)` exists in `self.query_context`. If so, immediately call `_generate_sql_with_context(...)`.

**Patch (targeted snippet):**

```python
confirm_synonyms = {"see the records","show them","list them","show me","just count","count only","count them"}

ctx_key = (conversation_id, doc_id)
if ctx_key in self.query_context and query_text.strip().lower() in confirm_synonyms:
    context = self.query_context[ctx_key]
    return self._generate_sql_with_context(query_text, context, datetime_context)
```

#### 2B) Lightweight typo tolerance in context path

* In `_generate_sql_with_context(...)`, when matching locations/names, prefer `LOWER(field) LIKE '%detroi%'` style where appropriate (most examples already use LIKE; this step is documentation—ensure the prompt mentions misspellings and shows a LIKE example, which it already does).

### Tests

Add: `tests/test_query_agent_guard.py`

```python
from query_agent import create_query_agent

def test_early_guard_applied(monkeypatch):
    agent = create_query_agent("QueryAgent")
    monkeypatch.setattr("query_agent.load_metadata", lambda d: {"fields":["Location (city)"],"duckdb_table_name":"t","record_count":1})
    s1 = {"conversation_id":"c1","doc_id":"d1","query_text":"how many are in detroit?","context":{},"datetime_context":{}}
    r1 = agent.process_query_request(s1)
    assert r1.get("clarification")
    s2 = {"conversation_id":"c1","doc_id":"d1","query_text":"see the records","context":{},"datetime_context":{}}
    r2 = agent.process_query_request(s2)
    assert r2.get("sql")
```

**Run tests:**

```
pytest -q
```

**Manual acceptance:** Repeat your exact 3‑turn scenario and verify a table appears.

---

## Phase 3 — UI Rendering Hardening

**Objective:** Ensure the chat never looks “stopped”.

### Frontend changes

Files:

* `AgentChat.js`

#### 3A) Three mutually‑exclusive render branches

* If `response.clarification` → show clarification text.
* Else if `response.rows && response.columns` → render table.
* Else → render `response.summary || response.error` as a message bubble.

#### 3B) Large result UX

* If `response.result_management.strategy === 'excel_download'`, show: a toast, a download link (from `download_url`), **and** a preview of first N rows (server already returns full rows; slice in UI).

### Tests (manual)

* **Start/restart the frontend dev server** if required.
* Trigger a >65‑row query and confirm you see a link + preview, not a blank turn.

---

## Phase 4 — “Make this a report” Handoff

**Objective:** Smoothly pivot from a query context to a report request.

### Backend (routing behavior uses existing files — no code edits here if routing already distinguishes ‘report’ intent). If you need intent keywords, add them only in:

Files:

* `orchestration_agent.py` (if required to improve `route_request`)

#### 4A) Router intent nudge (optional)

* Expand keywords for report intent ("make this a report", "create a report", "turn this into a report", "export as xlsx", "monthly/weekly summary").
* Keep implementation minimal—only change keyword list passed into or used by `route_request` if that list lives in `orchestration_agent.py` or associated util.

### Backend (report seeding)

Files:

* `report_agent.py`

#### 4B) Seed report from last query (non‑breaking)

* If `structured_input` includes `conversation_id` and you have a last‑turn SQL cached in memory, seed the simple config generator with that SQL. If not present, behavior is unchanged.
* Keep cache in `ReportAgent` as an in‑memory dict keyed by `(conversation_id, doc_id)`; update it whenever a report is produced.

**Minimal snippet for storing last SQL (optional small addition):** you may add a setter on `QueryAgent` later; for now Phase 4 can be skipped if you prefer keeping agents decoupled.

### Tests

* Manual: Query → “make this a report with monthly counts” → expect ReportAgent output aligned with the last filter context.

---

## Phase 5 — Agent Type Alignment (cleanup)

**Objective:** Reduce ambiguity/cost by aligning to the spec.

### Backend changes

Files:

* `orchestration_agent.py`
* `memory_agent.py`

#### 5A) Convert to Tool‑style behavior (no conversational retries)

* Remove LLM‑style retries, keep deterministic function calls to `route_request(...)` and DuckDB getters.
* Keep public method names and orchestrator interface unchanged.

### Tests

* Add unit tests for deterministic routing/memory lookup if you make logic changes; otherwise rely on existing tests.

---

## Smoke Test Checklist (end‑to‑end)

1. **Upload** a file.
2. Ask: “list hotels with discount > 15%.”
3. Ask: “how many are in Detroit?” → when asked, reply “see the records.”
4. Ask: “great—make this a report with monthly counts.”

**You must start/restart backend and frontend servers as needed** before each interactive test round.

---

## Commands & Notes

* **Backend tests:** `pytest -q`
* **If your app requires a running API for manual tests, please start/restart it now:**

  * Example: `python app.py` *(or your framework equivalent)*
* **Frontend dev server (if applicable):** start/restart before UI checks.

---

## Completion Criteria (per phase)

* Phase is **not** complete until:

  1. All listed unit tests pass, **and**
  2. You manually perform the acceptance steps and confirm behavior.

That’s it—apply Phase 1 first, run tests, and ping me if anything is unclear before proceeding to Phase 2.
