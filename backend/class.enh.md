# Classification Enhancement (Document: `class_enh.md`)

## Purpose

Enhance the document classification and naming strategy to:

* Improve identification and grouping of semantically similar documents
* Support reusability across sessions (e.g., monthly, quarterly financial reports)
* Enable conversational refinement of classification and naming
* Prepare for future modeling and comparison of documents with aligned schemas

---

## Background

Currently, documents uploaded via `/upload` are processed and analyzed, and a default type is assigned (often defaulting to `"document_type": "New"`). This lacks semantic grouping and causes friction when users want to:

* Compare documents across time (e.g., Q1 vs Q2 reports)
* Reuse existing queries or reports from similar documents
* Organize and retrieve reports by domain-specific types (e.g., "Hospital Finance")

To address this, the enhanced classification process will leverage:

* Existing `doc_registry` which includes field structure for all uploaded documents
* Field-level comparison logic to infer document similarity
* `ChatAgent`-driven dialog for user confirmation and classification refinement

---

## Proposed Enhancements

### 1. Proactive Schema-Based Matching

* **CRITICAL**: When a new document is uploaded, the system must **immediately and proactively** compare its fields to existing entries in the `doc_registry`
* **No user interaction required** - classification questions must be presented automatically in the upload response
* If a close match is found (e.g., 90%+ field overlap), **immediately** prompt the user via `ChatAgent`:

```text
This document appears to match a known type: "Hospital Finance Document". Should I classify it as the same?
```

* If no match is found, **immediately** prompt:

```text
What would you like to call this type of document? I classify documents so you can reuse queries and compare reports across time.
```

**Key Requirement**: The classification conversation must be **triggered automatically during upload**, not waiting for the user to manually ask "What type of document is this?"

### 2. Conversational Support for Reclassification

The `ChatAgent` must support the following user-driven reclassification flows:

* **Rename document type**

```text
Can you rename this document type to "Hospital Q2 Ledger"?
```

* **Reclassify document**

```text
This isn’t a finance report — reclassify it as "Quarterly Staffing".
```

The agent should:

* Validate the current `doc_id`
* Look up `document_type` and `document_type_code`
* Update metadata via backend utility (TBD)

### 3. List Known Types for Selection

If the user asks:

```text
What types of documents have I uploaded?
```

Or if clarification is needed during classification:

```text
You currently have the following document types:
- Hospital Finance Document
- Budget Template
- Monthly Staffing Report

Should I reuse one of these or create a new type?
```

This guidance will help users maintain consistent labeling and better future reuse.

### 4. Rename Queries or Reports

Support via `ChatAgent`:

* “Rename the ‘Q2 Spend’ query to ‘Q2 Vendor Spending’.”
* “Update the report name to ‘Staffing by Month’.”

→ Requires backend endpoint or utility to update saved metadata in `saved_queries` or `saved_reports`

---

## Backend Requirements (Future)

To support the above behaviors, the following enhancements are likely needed:

* Utility: `update_document_type(doc_id, new_type)`
* Utility: `rename_saved_query(query_id, new_name)`
* Utility: `rename_saved_report(report_id, new_name)`
* Accessor: `get_known_doc_types(user_id)`

No new endpoints or agents should be created unless explicitly authorized in this document.

---

## Agent Behavior Update

### Update Existing Agent: `ChatAgent`

* Add support for classification refinement dialogs
* Handle document type naming, suggestion, confirmation
* Handle renaming or reclassifying on request
* Maintain conversational flow while calling relevant utilities

Route: `POST /chat-agent`

No new agent or endpoint should be introduced unless this document is updated.

---

## Example Flows

### Upload → Auto Classify → Confirm

1. User uploads `Hosp_financesQ2_2025.xlsx`
2. Fields match `Hosp_financesQ1_2025.xlsx` at 95%
3. Agent says:

```text
Looks like this matches your previous "Hospital Finance Document". Should I classify it the same?
```

4. User: “Yes” → Classification is saved and doc\_registry is updated

### Rename Query

```text
User: Rename ‘Vendor Spend’ to ‘Q2 Vendor Spending’
→ Agent confirms and updates via backend utility
```

---

## Summary

This classification enhancement empowers users to:

* Maintain consistency across uploads
* Reuse naming logic and known types
* Support more intelligent document comparison
* Use `ChatAgent` for document hygiene and schema alignment

All behavior is routed through `ChatAgent` and `/chat-agent`. No new agents or endpoints should be created unless this document is revised.
