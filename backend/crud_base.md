# Delete CRUD Utilities (Admin-Only)

## Purpose

Enable simple backend delete operations to support cleaning up:

* Uploaded DuckDB tables
* Saved queries
* Saved reports
* Document registry metadata

This tool is intended for developer/test use only and will not be exposed to normal users.

---

## API Endpoints

### 1. Delete DuckDB Table

* **Method:** `POST`
* **Route:** `/delete-table`
* **Payload:**

```json
{
  "table_name": "hospital_ledger_fy2024_001"
}
```

* **Behavior:** Drops the specified DuckDB table if it exists.

---

### 2. Delete Saved Query

* **Method:** `POST`
* **Route:** `/delete-query`
* **Payload:**

```json
{
  "query_name": "Quarterly Vendor Spend"
}
```

* **Behavior:** Removes the saved query from `saved_queries`.

---

### 3. Delete Saved Report

* **Method:** `POST`
* **Route:** `/delete-report`
* **Payload:**

```json
{
  "report_name": "Monthly Spending Breakdown"
}
```

* **Behavior:** Removes the report definition from `saved_reports`.

---

### 4. Delete Doc Registry Entry

* **Method:** `POST`
* **Route:** `/delete-doc-metadata`
* **Payload:**

```json
{
  "doc_id": "hospital_ledger_fy2024_001"
}
```

* **Behavior:** Deletes document metadata from `doc_registry`.

---

## Security

* These routes should be limited to **internal/test use only**.
* Add a simple environment flag or token-based check to prevent misuse in production.

---

## Implementation Notes

* No frontend integration is planned.
* Logging should be added to each delete call to confirm and audit what was removed.
* Future enhancements may include bulk delete support and soft-delete options.
