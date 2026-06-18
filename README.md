# DBS Retail Banking RAG + Action Agent

A conversational AI prototype for DBS Bank using RAG + Actions.

## Quick Start

### 1. Install Dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment
Edit .env file with your API keys:
```
MISTRAL_API_KEY=your_key_here
LANGWATCH_API_KEY=your_key_here
```

### 3. Run Application
```powershell
cd ui
chainlit run chainlit_app.py -w
```

Visit http://localhost:8000

## Project Structure
```
dbs_banking_agent/
â”œâ”€â”€ knowledge_docs/     # FAQs and policies
â”œâ”€â”€ llm/               # Mistral AI integration
â”œâ”€â”€ rag/               # ChromaDB vector store
â”œâ”€â”€ ui/                # Chainlit interface
â”œâ”€â”€ audit/             # Logging and tracking
â”œâ”€â”€ logs/              # Auto-generated logs
â””â”€â”€ *.py               # Core modules
```

## Features
- FAQ answering with RAG
- Account actions (lock card, check balance)
- Prompt injection prevention
- Content moderation (Mistral AI)
- Multi-turn conversations
- LangWatch observability

## Theme Configuration

The application uses a custom blue theme. To modify the theme:

1. Edit `.chainlit/config.toml` for persistent theme changes
2. Or modify `ui/chainlit_app.py` (the `cl.set_defaults()` call)

Color palette:
- Primary: `#3b82f6` (Blue-500)
- Primary Hover: `#2563eb` (Blue-600)
- Secondary: `#60a5fa` (Blue-400)
- Error: `#ef4444` (Red-500 - kept red for UX convention)

