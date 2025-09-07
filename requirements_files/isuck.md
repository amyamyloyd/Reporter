# Fix Plan: LLM + Download Issues

## Problem Summary
- LLM filename generation broken due to missing `export_type` parameter
- Download opens new tab instead of downloading file
- Everything was working before but got corrupted during "fixes"

## Solution 1: Fix LLM Filename Generation
**Action:** Restore the `export_type` parameter to the `generate_query_name_with_llm()` function

**Why:** QueryAgent is calling `export_type="excel_export"` but the function signature doesn't support it, causing fallback to regex pattern instead of LLM-generated names.

**Files to modify:**
- `backend/app.py` - Add `export_type` parameter back to function signature
- Restore the Excel export prompt logic
- Restore the response handling for Excel filenames

## Solution 2: Fix Download Issue
**Action:** Use Frontend fetch + blob approach

**Why:** Current `Content-Disposition: attachment` approach isn't working - browsers treat it as display instead of download.

**Implementation:**
- Frontend: Use JavaScript to fetch the file URL
- Create blob from response
- Trigger download programmatically
- No backend changes needed

**Example approach:**
```javascript
async function downloadFile(url, filename) {
  const response = await fetch(url);
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(downloadUrl);
}
```

## Expected Results
- LLM generates semantic filenames like `costcenter_central_supply_20250906_190140.xlsx`
- Download button triggers actual file download to user's Downloads folder
- No more new tab opening or page refreshing

## Files to Modify
1. `backend/app.py` - Restore LLM function with export_type support
2. Frontend component - Implement fetch + blob download logic
