# 🚀 SuperMenu Implementation Plan - Step-by-Step

## Overview
This document provides a detailed, trackable implementation plan for the SuperMenu feature. Each step is designed to be testable and committable independently.

---

## 📋 Pre-Implementation Checklist

### Backend Database Schema Updates
- [x] Add `is_favorite BOOLEAN DEFAULT false` to `doc_registry` table
- [x] Add `is_favorite BOOLEAN DEFAULT false` to `queries` table  
- [x] Add `is_favorite BOOLEAN DEFAULT false` to `reports` table

### Backend Endpoint Implementation
- [x] Implement `PATCH /query/:id` endpoint for favorites toggle
- [x] Implement `PATCH /report/:id` endpoint for favorites toggle
- [x] Implement `POST /query/run` endpoint for direct SQL execution
- [x] Implement `POST /report/run` endpoint for direct report execution

---

## 🎯 Phase 1: Foundational UI Scaffolding

### Step 1.1: Create MainLayout Tab Structure
**File:** `frontend/src/components/layout/MainLayout.js`

**Tasks:**
- [x] Add tab navigation UI with 3 tabs: `ALL`, `CONTEXT`, `MODEL`
- [x] Implement tab state management with `useState`
- [x] Add tab switching logic
- [x] Style tabs with Tailwind CSS (active/inactive states)

**Acceptance Criteria:**
- [x] 3 tabs visible and clickable
- [x] Active tab highlighted
- [x] Tab content area ready for components

### Step 1.2: Create QueryListSection Component
**File:** `frontend/src/components/QueryListSection.js` (new)

**Props Interface:**
```javascript
{
  items: Array,           // queries or reports array
  type: String,          // 'query' or 'report'
  onRunItem: Function,   // callback for item execution
  onToggleFavorite: Function, // callback for favorite toggle
  showFavoritesOnly: Boolean, // filter state
  onToggleFavoritesFilter: Function // callback for filter toggle
}
```

**Tasks:**
- [x] Create component structure with props validation
- [x] Implement grouping by `document_type`
- [x] Add "Show 5 per group" logic with "More..." button
- [x] Add "Show Favorites Only" toggle
- [x] Implement sorting (default: `last_used desc` for queries, `last_generated desc` for reports)
- [x] Add column header click sorting
- [x] Style with Tailwind CSS

**Visual Elements:**
- [x] Usage count badges (`use_count` for queries, `generation_count` for reports)
- [x] Version highlighting (`is_current_version: true` = bold text + green background + checkmark)
- [x] Favorite star icons (clickable, filled/unfilled states)
- [x] Document type grouping headers

**Acceptance Criteria:**
- [x] Items grouped by document_type
- [x] 5 items per group with "More..." button
- [x] Sorting works on all columns
- [x] Favorites toggle works
- [x] Visual highlighting for current versions
- [x] Star icons toggle favorites

### Step 1.3: Create FileModelSelector Component
**File:** `frontend/src/components/FileModelSelector.js` (new)

**Props Interface:**
```javascript
{
  uploadedFiles: Array,  // from localStorage.recentUploads
  onSelectionChange: Function, // callback when selection changes
  selectedDatasets: Array // currently selected files
}
```

**Tasks:**
- [x] Read from `localStorage.recentUploads`
- [x] Display filename, json_filename, duckdb_table for each file
- [x] Add multi-select checkboxes
- [x] Implement selection state management
- [x] Style with Tailwind CSS

**Acceptance Criteria:**
- [x] Shows all uploaded files from localStorage
- [x] Multi-select checkboxes work
- [x] Selection state persists
- [x] Displays all required metadata fields

### Step 1.4: Integrate Components in MainLayout
**File:** `frontend/src/components/layout/MainLayout.js`

**Tasks:**
- [x] Import QueryListSection and FileModelSelector
- [x] Add state for queries, reports, and uploaded files
- [x] Implement data fetching for queries and reports
- [x] Add tab content rendering logic
- [x] Handle component props and callbacks

**Data Fetching:**
- [x] `GET /queries` on component mount
- [x] `GET /reports` on component mount
- [x] Read `localStorage.recentUploads` for MODEL tab

**Acceptance Criteria:**
- [x] All tabs render with correct data
- [x] Data loads on component mount
- [x] Components receive correct props
- [x] No console errors

### Step 1.5: Update Application Favicon
**File:** `frontend/public/index.html`

**Tasks:**
- [x] Change favicon from `analyst.svg` to `reporter.svg`
- [x] Copy `reporter.svg` to `frontend/public/` directory
- [x] Verify favicon displays correctly in browser

**Acceptance Criteria:**
- [x] Favicon shows `reporter.svg` icon
- [x] File exists in correct location
- [x] Browser displays new favicon after refresh

---

## 🎯 Phase 2: Click-to-Run Queries & Reports (MVP)

### Step 2.1: Implement Backend Run Endpoints
**File:** `backend/app.py`

**Tasks:**
- [x] Add `@app.post('/query/run')` endpoint
- [x] Accept full query object as payload
- [x] Execute SQL directly using DuckDB (bypass LLM)
- [x] Use existing `_determine_result_management()` logic
- [x] Return same format as existing query endpoint

**Payload Format:**
```json
{
  "query_name": "string",
  "sql": "string",
  "schema": ["field1", "field2"],
  "document_type": "string"
}
```

**File:** `backend/app.py`

**Tasks:**
- [x] Add `@app.post('/report/run')` endpoint
- [x] Accept full report config as payload
- [x] Execute report using existing `build_report()` logic
- [x] Return same format as existing report endpoint

**Acceptance Criteria:**
- [x] Endpoints accept full objects
- [x] SQL executes directly (no LLM calls)
- [x] Results match existing query/report format
- [x] Error handling for invalid SQL/config

### Step 2.2: Implement Favorites Backend Endpoints
**File:** `backend/app.py`

**Tasks:**
- [x] Add `@app.patch('/query/:id')` endpoint
- [x] Accept `{ "is_favorite": true|false }` payload
- [x] Update DuckDB queries table
- [x] Return updated query object

**File:** `backend/app.py`

**Tasks:**
- [x] Add `@app.patch('/report/:id')` endpoint
- [x] Accept `{ "is_favorite": true|false }` payload
- [x] Update DuckDB reports table
- [x] Return updated report object

**Acceptance Criteria:**
- [x] PATCH endpoints work for both queries and reports
- [x] Database updates persist
- [x] Returns updated object
- [x] Error handling for invalid IDs

### Step 2.3: Add Loading States and Error Handling
**File:** `frontend/src/components/QueryListSection.js`

**Tasks:**
- [x] Add loading state for item execution
- [x] Show spinner with "Doing this work so you don't have to" message
- [x] Add error handling for failed executions
- [x] Display "Query failed - ask me again what you are looking for" on error

**Loading UI:**
- [x] Disable item during execution
- [x] Show spinner overlay
- [x] Display loading message

**Error UI:**
- [x] Show error message in chat area
- [x] Reset loading state
- [x] Allow retry

**Acceptance Criteria:**
- [x] Loading states work for all items
- [x] Error messages appear in chat
- [x] UI doesn't break on errors
- [x] Loading states clear properly

### Step 2.4: Integrate with AutoGenChat for Results
**File:** `frontend/src/components/layout/MainLayout.js`

**Tasks:**
- [x] Implement `handleRunItem(item)` method
- [x] Call appropriate `/query/run` or `/report/run` endpoint
- [x] Forward results to AutoGenChat component
- [x] Handle loading and error states

**Result Integration:**
- [x] Use existing result display logic from AutoGenChat
- [x] Results appear exactly as they do today
- [x] ≤65 rows: HTML table display
- [x] >65 rows: Excel download trigger
- [x] No difference from existing Upload → Query → Result flow

**Acceptance Criteria:**
- [x] Clicking items executes queries/reports
- [x] Results appear in chat area
- [x] Format matches existing behavior exactly
- [x] Excel downloads work for large results
- [x] User cannot tell difference from existing flow

---

## 🎯 Phase 3: MVP Enhancements

### Step 3.1: Implement Modal for Large Lists
**File:** `frontend/src/components/QueryListSection.js`

**Tasks:**
- [ ] Add modal trigger when >30 items in group
- [ ] Create scrollable modal with search input
- [ ] Add filter functionality in modal
- [ ] Use Bootstrap or AdminLTE modal component

**Modal Features:**
- [ ] Search by name, tags, document_type
- [ ] Filter by favorites
- [ ] Sort by all columns
- [ ] Pagination or infinite scroll

**Acceptance Criteria:**
- [ ] Modal opens when >30 items
- [ ] Search and filter work in modal
- [ ] Modal closes properly
- [ ] Selection persists when modal closes

### Step 3.2: Add Version Management Display
**File:** `frontend/src/components/QueryListSection.js`

**Tasks:**
- [ ] Display "Uploaded: date" in light gray text
- [ ] Display "Version: X" in light gray text
- [ ] Highlight current versions with:
  - [ ] Bold text
  - [ ] Light-green background
  - [ ] ✅ checkmark or tag

**Acceptance Criteria:**
- [ ] Version info visible on all items
- [ ] Current versions clearly highlighted
- [ ] Visual hierarchy clear

### Step 3.3: Add Prompt-to-Run Feature (Future Alpha)
**File:** `frontend/src/components/AutoGenChat.js`

**Tasks:**
- [ ] Detect `run <<query_name>>` command in chat input
- [ ] Look up query by name
- [ ] Execute via `/query/run` endpoint
- [ ] Display results using existing formatting

**Acceptance Criteria:**
- [ ] Command detection works
- [ ] Query lookup by name works
- [ ] Results display normally
- [ ] Error handling for unknown queries

---

## 🧪 Testing Strategy

### Unit Tests
- [ ] QueryListSection component rendering
- [ ] FileModelSelector component selection logic
- [ ] MainLayout tab switching
- [ ] Backend endpoint responses

### Integration Tests
- [ ] Full query execution flow
- [ ] Full report execution flow
- [ ] Favorites toggle persistence
- [ ] Error handling scenarios

### User Acceptance Tests
- [ ] User can browse all saved queries/reports
- [ ] User can filter by document type and favorites
- [ ] User can execute queries and see results
- [ ] Results appear identical to existing flow
- [ ] User can select files for modeling

---

## 📊 Success Metrics

### Phase 1 Complete When:
- [ ] All 3 tabs render with data
- [ ] Items group and sort correctly
- [ ] Favorites toggle works (UI only)
- [ ] No console errors

### Phase 2 Complete When:
- [x] Clicking items executes queries/reports
- [x] Results appear in chat area
- [x] Favorites persist in database
- [x] Loading and error states work
- [x] Results format matches existing behavior exactly

**✅ PHASE 2 COMPLETE** - All SuperMenu click-to-run functionality working perfectly!

### Phase 3 Complete When:
- [ ] Modal works for large lists
- [ ] Version info displays correctly
- [ ] All visual highlighting works
- [ ] User experience is smooth and intuitive

---

## 🚨 Risk Mitigation

### Technical Risks:
- **Backend endpoint conflicts**: Use `/query/run` and `/report/run` to avoid conflicts
- **Result format changes**: Reuse existing formatting logic exactly
- **Performance with large lists**: Implement pagination and modal early

### User Experience Risks:
- **Confusion with existing flow**: Ensure results appear identical
- **Loading state clarity**: Use clear messaging and spinners
- **Error recovery**: Provide clear error messages and retry options

---

## 📝 Implementation Notes

### Code Standards:
- Follow existing React patterns in the codebase
- Use Tailwind CSS for all styling
- Maintain 30% comment ratio
- Use functional components with hooks
- Implement proper error boundaries

### Database Considerations:
- Add `is_favorite` columns manually before starting
- Test with existing data
- Ensure backward compatibility

### Performance Considerations:
- Implement pagination early
- Use React.memo for list components
- Debounce search inputs
- Lazy load modal content

---

## ✅ Ready to Start

This implementation plan provides:
- Clear, trackable steps
- Specific acceptance criteria
- Risk mitigation strategies
- Testing approach
- Success metrics

Each step can be implemented and tested independently, allowing for incremental progress and early feedback.
