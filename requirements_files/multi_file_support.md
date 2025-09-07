# 📦 Multi-File Upload Spec – Phase 2

> 🧠 Audience: Cursor AI Senior Developer
> 🛠 Context: This is a **simple single-user tool** for uploading Excel files, modeling them, querying, and reporting (future agents: model, query, report). This is not an enterprise-grade app. Keep logic and UI **simple and minimal**.

---

## ✅ USE CASE: Multi-File Upload

### 🔹 Trigger

User uploads **multiple `.xlsx` files** via the existing upload UI.

---

### 🔹 Backend: `/upload` Endpoint

* Accepts multiple files.
* Validates each.
* Generates `.json` metadata for each file.
* Determines `doc_type` using registry.
* Updates `localStorage.recentUploads[]` with:

  ```json
  {
    "filename": "Projects_2025.xlsx",
    "json_filename": "Projects_2025.json",
    "doc_type": "Projects",
    "duckdb_table": "projects_2025",
    "fields": ["Project Name", "Start Date"],
    "upload_time": "<ISO timestamp>"
  }
  ```
* Returns response:

  ```json
  {
    "status": "success",
    "files": [
      {
        "filename": "Projects_2025.xlsx",
        "json_filename": "Projects_2025.json",
        "doc_type": "Projects",
        "status": "known", // or "new"
        "fields": [...],
        "duckdb_table": "projects_2025"
      }
    ]
  }
  ```

---

### 🔹 Frontend Behavior: `AgentChat.js`

1. Load response files:

   ```js
   const sessionFiles = response.files.map(file => ({ ...file }));
   ```

2. For each file:

   * If `status === 'known'`: display

     > “✅ `[filename]` is ready to query.”
   * If `status === 'new'`: prompt user

     > “🆕 This file looks new. Please describe it.”

3. Agent gathers:

   * User description
   * Suggestions from OpenAI for `doc_type` and unique 3-letter code
   * Confirmation from user (or present choices)

4. Final updates:

   * `.json` file is created/updated
   * Entry added to `localStorage.recentUploads[]`
   * `doc_registry` version updated

5. Confirmation message:

   ```text
   You uploaded 3 files:
   ✅ Projects_2025.xlsx — ready to query.
   🆕 Budget_2025.xlsx — unknown. Let’s assign a document type.
   ```

---

### 🔹 Important Constraints

* Do NOT reprocess `.xlsx` if `.json` and DuckDB table already exist.
* Use `.json` metadata + `duckdb_table` info to proceed.
* Maximum \~5 files expected per session.
* No async coordination needed.

---

### 🔹 Result

All files (known or new) are:

* Fully available to AgentChat.
* Properly stored with metadata.
* Ready for future agents: `model`, `query`, `report`.

---

### 🔚 Dev Note

This is a focused MVP for internal use. Avoid overengineering:

* No multi-user session support.
* No permissions.
* Keep prompts and flows concise and understandable.
