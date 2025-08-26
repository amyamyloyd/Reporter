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
