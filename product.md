# AI-Powered Excel Reporting POC - Cursor Development Guide

## High-Level System Description
Build a web application for non-technical users to upload Excel files, use AI agents to analyze data relationships, and generate formatted Excel reports. The system uses Microsoft AutoGen agents with ChatGPT-4 for conversational data modeling and query building.

**Core Flow**: Upload Excel → Agent File Analysis → Build SQLite Model → Explain Model → Agent Query Building → Execute Query → Generate Excel Report → Download

**Key Constraint**: Single-session system - no data persistence beyond temporary processing.

## Tech Stack (FIXED - DO NOT CHANGE)
- **Frontend**: React 18 + `xlsx` (SheetJS) + `axios` + Tailwind CSS
- **Backend**: Python 3.11 + FastAPI + Microsoft AutoGen + pandas + SQLite + `openpyxl`
- **AI**: ChatGPT-4 (cost-optimized, not GPT-4o)
- **Deployment**: Azure Static Web Apps (React) + Azure App Service (FastAPI)

## Hybrid Development Approach - 3 Phases

### PHASE 1: CORE FOUNDATION (Build Stable Base)
**GOAL**: Create reusable infrastructure that won't need changes later

#### Backend Foundation (`/backend/`)

**File: `excel_processor.py`**
```python
# ONLY handle Excel file parsing and metadata extraction
# DO NOT add business logic, agents, or complex processing
import pandas as pd

def extract_file_metadata(uploaded_files):
    """Extract basic sheet names, field names, and types from Excel files"""
    # Return: {"filename": {"sheets": {"sheet_name": {"fields": [], "types": {}}}}}
    pass

def validate_excel_files(files):
    """Check file size (<50MB), type (.xlsx/.xls), count (<=5)"""
    pass
```

**File: `sqlite_manager.py`**
```python
# ONLY handle SQLite database operations
# DO NOT add query logic or agent interactions
import sqlite3
import pandas as pd

def create_memory_database():
    """Create in-memory SQLite connection"""
    pass

def dataframe_to_table(conn, df, table_name):
    """Convert pandas DataFrame to SQLite table using df.to_sql()"""
    pass
```

**File: `app.py`**
```python
# ONLY basic FastAPI setup and single upload endpoint
# DO NOT add agent endpoints or complex logic yet
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Basic file upload that returns metadata only"""
    # Use excel_processor.extract_file_metadata()
    pass

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

#### Frontend Foundation (`/frontend/src/`)

**File: `api/client.js`**
```javascript
// ONLY axios configuration and basic API helpers
// DO NOT add complex business logic
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' }
});

export const uploadFiles = async (files) => {
  // Basic file upload function
};
```

**File: `components/layout/MainLayout.js`**
```javascript
// ONLY layout structure with large agent chat area
// DO NOT add business logic or complex interactions
import React from 'react';

function MainLayout({ children, agentPanel }) {
  return (
    <div className="flex h-screen">
      {/* Left side: Content (40%) */}
      <div className="w-2/5 p-4 overflow-y-auto">
        {children}
      </div>
      
      {/* Right side: Agent Chat (60% - LARGE REAL ESTATE) */}
      <div className="w-3/5 border-l border-gray-300 p-4">
        {agentPanel}
      </div>
    </div>
  );
}

export default MainLayout;
```

**File: `App.js`**
```javascript
// ONLY basic routing and layout integration
// DO NOT add complex state management or business logic
import React from 'react';
import MainLayout from './components/layout/MainLayout';

function App() {
  return (
    <div className="App">
      <MainLayout>
        <div>Content will go here in Phase 2</div>
      </MainLayout>
      <div>Agent panel will go here in Phase 2</div>
    </div>
  );
}

export default App;
```

**CURSOR CONSTRAINTS FOR PHASE 1:**
```
Build foundation components only. Target these files specifically:
- @backend/excel_processor.py (Excel parsing only)
- @backend/sqlite_manager.py (SQLite operations only)  
- @backend/app.py (basic FastAPI + /upload endpoint only)
- @frontend/src/api/client.js (axios setup only)
- @frontend/src/components/layout/MainLayout.js (60% agent area layout)
- @frontend/src/App.js (basic structure only)

DO NOT:
- Add AutoGen agents yet
- Add complex UI components  
- Modify .env files or configuration
- Add query logic or report generation
- Create database schemas or persistence

STOP after building these 6 files. Test upload functionality before proceeding.
```

---

### PHASE 2A: FILE UPLOAD & ANALYSIS (First Vertical Slice)
**GOAL**: Complete upload → agent analysis → JSON storage workflow

#### Add Agent Logic (`/backend/agents/`)

**File: `file_analyzer.py`**
```python
# ONLY file-by-file analysis agent
# DO NOT add query building or report generation
from autogen import AssistantAgent, UserProxyAgent

def create_file_analyzer():
    """Create AutoGen agent for analyzing one file at a time"""
    config = [{
        "model": "gpt-4",  # Cost-optimized, not gpt-4o
        "api_key": os.environ["OPENAI_API_KEY"],
        "max_tokens": 500,
        "temperature": 0.1
    }]
    
    system_message = """You analyze Excel files one at a time. For each file:
1. Ask user what the file represents  
2. Identify key reporting fields (metrics like cost, quantity)
3. Identify join fields that connect to other files
4. Structure response as JSON: {"fields": {"field_name": {"type": "string", "role": "join_field|reporting_field|primary_id"}}}
Keep responses conversational and concise."""
    
    return AssistantAgent("FileAnalyzer", llm_config={"config_list": config}, system_message=system_message)
```

#### Add UI Components

**File: `components/FileUploader.js`**
```javascript
// ONLY file upload with validation
// DO NOT add agent interactions or complex state management
import React, { useState } from 'react';
import * as XLSX from 'xlsx';
import { uploadFiles } from '../api/client';

function FileUploader({ onFilesUploaded }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);

  const handleFileUpload = async (e) => {
    const selectedFiles = Array.from(e.target.files);
    
    // Validate: max 5 files, <50MB each, .xlsx/.xls only
    const validFiles = selectedFiles.filter(f => 
      f.size < 50 * 1024 * 1024 && 
      (f.name.endsWith('.xlsx') || f.name.endsWith('.xls'))
    );
    
    if (validFiles.length !== selectedFiles.length) {
      alert('Some files were rejected: check size (<50MB) and format (.xlsx/.xls)');
    }
    
    if (validFiles.length > 5) {
      alert('Maximum 5 files allowed');
      return;
    }

    setFiles(validFiles);
    setUploading(true);
    
    try {
      const result = await uploadFiles(validFiles);
      onFilesUploaded(result);
    } catch (error) {
      alert('Upload failed: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg">
      <input 
        type="file" 
        multiple 
        accept=".xlsx,.xls" 
        onChange={handleFileUpload}
        className="hidden"
        id="file-upload"
      />
      <label 
        htmlFor="file-upload" 
        className="cursor-pointer block text-center p-4 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        {uploading ? 'Uploading...' : 'Select Excel Files (Max 5, <50MB each)'}
      </label>
      
      {files.length > 0 && (
        <ul className="mt-4">
          {files.map(f => (
            <li key={f.name} className="text-sm text-gray-600">✓ {f.name}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default FileUploader;
```

**File: `components/AgentChat.js`**
```javascript
// ONLY agent conversation UI
// DO NOT add query building or report generation
import React, { useState } from 'react';
import axios from 'axios';

function AgentChat({ files, onAnalysisComplete }) {
  const [messages, setMessages] = useState([]);
  const [currentInput, setCurrentInput] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);

  const sendMessage = async () => {
    if (!currentInput.trim()) return;
    
    setAnalyzing(true);
    try {
      const response = await axios.post('/analyze-file', {
        file_info: files[currentFileIndex],
        user_input: currentInput,
        conversation_history: messages
      });
      
      setMessages([...messages, 
        { role: 'user', content: currentInput },
        { role: 'agent', content: response.data.response }
      ]);
      
      if (response.data.file_complete) {
        // Move to next file or complete analysis
        if (currentFileIndex < files.length - 1) {
          setCurrentFileIndex(currentFileIndex + 1);
        } else {
          onAnalysisComplete(response.data.analysis_results);
        }
      }
    } catch (error) {
      alert('Analysis failed: ' + error.message);
    } finally {
      setAnalyzing(false);
    }
    
    setCurrentInput('');
  };

  return (
    <div className="flex flex-col h-full">
      <div className="bg-gray-100 p-3 border-b">
        <h2 className="font-bold">AI Assistant</h2>
        {files.length > 0 && (
          <p className="text-sm text-gray-600">
            Analyzing: {files[currentFileIndex]?.name} ({currentFileIndex + 1}/{files.length})
          </p>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`p-3 rounded ${
            msg.role === 'user' ? 'bg-blue-100 ml-8' : 'bg-gray-100 mr-8'
          }`}>
            <div className="font-semibold text-sm mb-1">
              {msg.role === 'user' ? 'You' : 'AI Assistant'}
            </div>
            <div>{msg.content}</div>
          </div>
        ))}
      </div>
      
      <div className="border-t p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={currentInput}
            onChange={e => setCurrentInput(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && sendMessage()}
            placeholder="Describe this file or answer the agent's question..."
            className="flex-1 border border-gray-300 rounded px-3 py-2"
            disabled={analyzing}
          />
          <button
            onClick={sendMessage}
            disabled={analyzing || !currentInput.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            {analyzing ? 'Thinking...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default AgentChat;
```

#### Add Backend Endpoints

**Add to `app.py`:**
```python
# ADD these endpoints to existing app.py
# DO NOT modify existing /upload endpoint

@app.post("/analyze-file")
async def analyze_file(request: dict):
    """Handle file-by-file agent analysis"""
    # Use file_analyzer.py to process one file
    # Return agent response and completion status
    pass

@app.post("/save-analysis")
async def save_analysis(analysis: dict):
    """Save analysis results to temporary JSON"""
    # Store in memory or temp file for session
    pass
```

**CURSOR CONSTRAINTS FOR PHASE 2A:**
```
Complete file upload and analysis workflow. Target these files:
- @backend/agents/file_analyzer.py (AutoGen file analysis only)
- @frontend/src/components/FileUploader.js (upload with validation only)
- @frontend/src/components/AgentChat.js (conversation UI only)
- Add /analyze-file and /save-analysis to @backend/app.py

DO NOT:
- Add data modeling or SQLite operations yet
- Add query building or report generation
- Modify Phase 1 foundation files
- Add complex state management

STOP after completing agent analysis. Test file-by-file conversation before proceeding.
```

---

### PHASE 2B: DATA MODEL BUILDING (Second Vertical Slice)
**GOAL**: Build SQLite model from analysis → explain to user → validate

#### Add Data Model Builder

**File: `data_modeler.py`**
```python
# ONLY build SQLite model from analysis results
# DO NOT add query execution or report generation
from sqlite_manager import create_memory_database, dataframe_to_table
import pandas as pd

def build_data_model(files_metadata, analysis_results):
    """Build SQLite database from Excel files and analysis"""
    conn = create_memory_database()
    
    # Convert each sheet to SQLite table
    # Store relationships for query building
    
    return conn, relationship_map

def generate_model_explanation(analysis_results):
    """Create human-readable explanation of data model"""
    # Return explanation text for agent to present
    pass
```

#### Add Model Explanation Agent

**File: `agents/model_explainer.py`**
```python
# ONLY explain data model to user
# DO NOT add query building logic
from autogen import AssistantAgent

def create_model_explainer():
    """Agent that explains the built data model"""
    system_message = """You explain data models to non-technical users. Given analysis results:
1. Summarize what data was found
2. Explain relationships between files  
3. List key metrics available for reporting
4. Ask for confirmation or corrections
Keep explanations simple and visual using emojis."""
    
    return AssistantAgent("ModelExplainer", system_message=system_message)
```

#### Add Model Validation UI

**File: `components/ModelValidator.js`**
```javascript
// ONLY model explanation and validation
// DO NOT add query interface
import React, { useState } from 'react';

function ModelValidator({ modelData, onValidated }) {
  const [validated, setValidated] = useState(false);

  const handleValidation = (isCorrect) => {
    if (isCorrect) {
      setValidated(true);
      onValidated(modelData);
    } else {
      // Allow corrections
      onValidated(null);
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Data Model Summary</h2>
      
      {/* Display model explanation from agent */}
      <div className="bg-gray-50 p-4 rounded mb-4">
        {modelData.explanation}
      </div>
      
      <div className="space-x-4">
        <button 
          onClick={() => handleValidation(true)}
          className="px-4 py-2 bg-green-500 text-white rounded"
        >
          ✓ Model Looks Correct
        </button>
        <button 
          onClick={() => handleValidation(false)}
          className="px-4 py-2 bg-red-500 text-white rounded"
        >
          ✗ Need to Fix Something
        </button>
      </div>
    </div>
  );
}

export default ModelValidator;
```

**CURSOR CONSTRAINTS FOR PHASE 2B:**
```
Complete data model building and validation. Target these files:
- @backend/data_modeler.py (SQLite model building only)
- @backend/agents/model_explainer.py (explanation agent only)
- @frontend/src/components/ModelValidator.js (validation UI only)
- Add /build-model and /explain-model endpoints to @backend/app.py

DO NOT:
- Add query building or execution
- Add report generation
- Modify previous phase files
- Add complex model editing

STOP after model validation. Test model explanation before proceeding.
```

---

### PHASE 3: QUERY & REPORT GENERATION (Final Vertical Slice)
**GOAL**: Complete the workflow with agent-assisted querying and Excel report generation

#### Add Query Assistant

**File: `agents/query_assistant.py`**
```python
# ONLY query building assistance
# DO NOT add report formatting logic
def create_query_assistant():
    """Agent that helps build SQL queries"""
    system_message = """You help users build SQL queries for their data model. 
Given the model schema and relationships:
1. Understand what user wants to analyze
2. Suggest appropriate SQL queries
3. Explain what the query will return
4. Handle common business questions like 'total cost by company'
Keep technical details simple."""
```

#### Add Report Generator

**File: `report_generator.py`**
```python
# ONLY Excel report generation
# DO NOT add query logic or agent interactions
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, PatternFill

def create_excel_report(query_results, report_title="Analysis Report"):
    """Generate formatted Excel file from query results"""
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    
    # Add professional formatting
    # Headers, borders, number formatting
    # Return bytes for download
    
    return excel_bytes

def format_worksheet(ws, data, headers):
    """Apply professional formatting to worksheet"""
    # Header styling, borders, alternating row colors
    pass
```

#### Add Query Interface

**File: `components/QueryInterface.js`**
```javascript
// ONLY query building and execution UI
import React, { useState } from 'react';

function QueryInterface({ modelData, onQueryExecuted }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const executeQuery = async () => {
    // Execute SQL query
    // Display results
  };

  const generateReport = async () => {
    setGeneratingReport(true);
    try {
      const response = await axios.post('/generate-report', { 
        query_results: results,
        report_title: 'Data Analysis Report'
      }, { responseType: 'blob' });
      
      // Trigger download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'analysis_report.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      setGeneratingReport(false);
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">Query Your Data</h2>
      
      {/* Agent chat for query building */}
      <div className="mb-6">
        {/* Query building conversation */}
      </div>
      
      {results && (
        <div className="mt-6">
          <h3 className="font-bold mb-2">Results:</h3>
          {/* Display query results */}
          
          <button 
            onClick={generateReport}
            disabled={generatingReport}
            className="mt-4 px-4 py-2 bg-green-500 text-white rounded"
          >
            {generatingReport ? 'Generating...' : 'Download Excel Report'}
          </button>
        </div>
      )}
    </div>
  );
}

export default QueryInterface;
```

#### Add Final Endpoints

**Add to `app.py`:**
```python
@app.post("/execute-query")
async def execute_query(query_request: dict):
    """Execute SQL query against data model"""
    # Use SQLite connection from model
    # Return query results
    pass

@app.post("/generate-report")
async def generate_report(report_request: dict):
    """Generate Excel report from query results"""
    # Use report_generator.py
    # Return Excel file for download
    pass
```

**CURSOR CONSTRAINTS FOR PHASE 3:**
```
Complete query and report generation. Target these files:
- @backend/agents/query_assistant.py (query building agent only)
- @backend/report_generator.py (Excel generation only)
- @frontend/src/components/QueryInterface.js (query UI and download only)
- Add /execute-query and /generate-report to @backend/app.py

DO NOT:
- Modify any previous phase files
- Add complex report customization
- Change database schema or model structure

STOP after completing Excel download. Test complete workflow.
```

---

## Critical Cursor Management Rules

### Global Constraints (ALL PHASES):
```
NEVER modify these files:
- .env or environment variables
- package.json or requirements.txt  
- Configuration files
- Port numbers (8000 for backend, 3000 for frontend)
- API base URLs

ALWAYS:
- Use exact file paths specified (@backend/file.py)
- Follow "DO NOT" lists strictly
- Stop at phase completion points
- Test functionality before proceeding
```

### File Organization:
```
/backend/
├── app.py                    # FastAPI main app
├── excel_processor.py        # Phase 1
├── sqlite_manager.py         # Phase 1  
├── data_modeler.py          # Phase 2B
├── report_generator.py      # Phase 3
└── agents/
    ├── file_analyzer.py     # Phase 2A
    ├── model_explainer.py   # Phase 2B
    └── query_assistant.py   # Phase 3

/frontend/src/
├── App.js                   # Phase 1
├── api/client.js           # Phase 1
├── components/
    ├── layout/MainLayout.js # Phase 1
    ├── FileUploader.js      # Phase 2A
    ├── AgentChat.js         # Phase 2A
    ├── ModelValidator.js    # Phase 2B
    └── QueryInterface.js    # Phase 3
```

### Testing Checkpoints:
- **Phase 1**: File upload returns metadata
- **Phase 2A**: Agent analyzes files and saves results
- **Phase 2B**: SQLite model builds and explains correctly  
- **Phase 3**: Queries execute and Excel downloads

This phased approach ensures working software at each step while keeping Cursor focused on bounded tasks.