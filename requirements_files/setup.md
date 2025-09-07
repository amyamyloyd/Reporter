# CURSOR: CREATE COMPLETE PROJECT FROM SCRATCH

## YOU MUST EXECUTE THESE COMMANDS IN ORDER

This is an **empty repository**. You need to create the entire project structure, virtual environment, and install all dependencies. **DO NOT SKIP ANY STEPS**.

---

## STEP 1: CREATE PROJECT STRUCTURE

Create these folders and files exactly as specified:

```
ai-excel-reporting-poc/
├── backend/
│   ├── agents/
│   ├── requirements.txt
│   ├── .env.example  
│   └── app.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   └── layout/
│   │   ├── api/
│   │   └── utils/
│   ├── package.json
│   └── .env.example
├── .gitignore
└── README.md
```

---

## STEP 2: CREATE BACKEND FILES

### Create `backend/requirements.txt`:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0
pyautogen==0.2.0
openai==1.3.0
pandas==2.1.3
openpyxl==3.1.2
python-multipart==0.0.6
pydantic==2.5.0
python-dotenv==1.0.0
```

### Create `backend/.env.example`:
```env
OPENAI_API_KEY=your_openai_api_key_here
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
```

### Create `backend/app.py`:
```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="AI Excel Reporting API", version="1.0.0")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "AI Excel Reporting API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "environment": os.getenv("ENVIRONMENT", "development")}

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """File upload endpoint with validation"""
    # Validate file count
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed")
    
    file_info = []
    for file in files:
        # Validate file size (50MB limit)
        if file.size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File {file.filename} exceeds 50MB limit")
        
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not an Excel file")
        
        file_info.append({
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type
        })
    
    return {"message": f"Received {len(files)} files", "files": file_info}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## STEP 3: CREATE FRONTEND FILES

### Create `frontend/package.json`:
```json
{
  "name": "ai-excel-reporting-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "xlsx": "^0.18.5",
    "axios": "^1.6.0",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8000"
}
```

### Create `frontend/.env.example`:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

### Create `frontend/tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### Create `frontend/postcss.config.js`:
```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### Create `frontend/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

### Create `frontend/src/index.js`:
```javascript
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

### Create `frontend/src/App.js`:
```javascript
import React from 'react';

function App() {
  return (
    <div className="App">
      <div className="flex h-screen bg-gray-50">
        {/* Main content - 40% */}
        <div className="w-2/5 bg-white p-6">
          <h1 className="text-2xl font-bold mb-4">AI Excel Reporting</h1>
          <p className="text-gray-600 mb-4">Upload Excel files for AI-powered analysis</p>
          <div className="p-8 border-2 border-dashed border-gray-300 rounded-lg text-center">
            <p className="text-gray-500">File uploader will be added in Phase 2A</p>
          </div>
        </div>
        
        {/* Agent panel - 60% */}
        <div className="w-3/5 border-l border-gray-200 bg-white">
          <div className="p-6">
            <h2 className="text-lg font-semibold text-blue-800 mb-2">AI Assistant</h2>
            <p className="text-sm text-blue-600 mb-4">Ready to help analyze your Excel files</p>
            <div className="h-96 flex items-center justify-center border rounded">
              <p className="text-gray-500 text-center">
                Agent chat will be added in Phase 2A<br/>
                <span className="text-sm">(This panel has 60% of screen width)</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
```

### Create `frontend/public/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="AI-powered Excel reporting tool" />
    <title>AI Excel Reporting</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
```

---

## STEP 4: CREATE CONFIGURATION FILES

### Create `.gitignore`:
```
# Dependencies
node_modules/
venv/
__pycache__/
*.pyc

# Environment files
.env
.env.local

# Build outputs
build/
dist/

# IDE files
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
```

### Create `README.md`:
```markdown
# AI Excel Reporting POC

AI-powered Excel analysis with conversational agents.

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm start
```

## Tech Stack
- React 18 + Tailwind CSS
- Python 3.11 + FastAPI + AutoGen
- SQLite + pandas + openpyxl
```

---

## STEP 5: **MANDATORY SETUP COMMANDS**

After creating all files, **YOU MUST RUN THESE COMMANDS**:

### Backend Setup:
```bash
cd backend
python -m venv venv
```

**For Windows:**
```bash
venv\Scripts\activate
```

**For Mac/Linux:**
```bash
source venv/bin/activate
```

**Then install dependencies:**
```bash
pip install -r requirements.txt
cp .env.example .env
```

### Frontend Setup:
```bash
cd frontend
npm install
cp .env.example .env
```

---

## STEP 6: VERIFICATION

**Test the setup by running:**

### Start Backend (in backend folder with venv activated):
```bash
python app.py
```
**Should show:** `Application startup complete`

### Start Frontend (in frontend folder):
```bash
npm start
```
**Should open:** http://localhost:3000

### Test API:
Visit: http://localhost:8000/health
**Should return:** `{"status": "healthy"}`

---

## SUCCESS CRITERIA

✅ Backend runs on port 8000  
✅ Frontend runs on port 3000  
✅ Health endpoint responds  
✅ React app shows 60/40 layout  
✅ No console errors  

**ONLY AFTER THIS WORKS, proceed with phase-based development.**

---

## IMPORTANT NOTES FOR CURSOR

1. **CREATE ALL FILES FIRST** - Don't skip any files
2. **RUN THE SETUP COMMANDS** - Virtual environment and npm install are mandatory
3. **TEST EVERYTHING** - Both servers must start successfully
4. **DO NOT MODIFY** - .env files, ports, or API URLs after creation
5. **STOP HERE** - Don't add business logic until setup is verified

**This is the foundation. Get this working before any development phases.**