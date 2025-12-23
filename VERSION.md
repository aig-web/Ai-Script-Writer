# ScriptAI Studio - Version History

## Current Version: 2.0.0

**Release Date:** December 23, 2024
**Git Branch:** main
**Last Commit:** Version 2.0 - Per-script chat, Supabase persistence, session history

---

## Version 2.0.0 - Chat & Persistence Update

### New Features
- **Per-Script Chat**: Each of the 3 scripts has its own chat interface
  - Click "Chat" button to open chat panel below script
  - Ask Claude to edit specific parts or rewrite the entire script
  - Chat history saved per script
- **Supabase Session Persistence**: Full session management with database
  - Auto-save on generation (no manual save button needed)
  - Sessions stored with: topic, mode, notes, research, scripts, chat history
  - Files (PDFs, TXT) content stored with sessions
- **Session History**: Click on any topic in history to restore complete state
  - Loads all data: topic, notes, research, scripts, chat messages
  - Resume where you left off without re-running the pipeline
  - Delete unwanted sessions

### Technical Changes
- New Supabase tables: `sessions`, `session_files`, `session_scripts`, `chat_messages`
- Backend: `session_service.py` for session CRUD operations
- Backend: `script_chat.py` for Claude-powered script editing
- New API endpoints: `/sessions`, `/chat`, session management
- Frontend: Replaced localStorage with Supabase API calls

### Migration Notes
- Run the updated `supabase_schema.sql` in your Supabase SQL Editor
- Old localStorage history will not be migrated (start fresh)

---

## Version 1.0.0 - Base Release

### Features
- **Multi-Angle Script Generation**: Generates 3 viral scripts with 3 different angles, each with 5 unique hooks
- **Research Orchestrator**: Multi-stage research with topic type detection (A/B/C/D)
  - Type A: Specific topics (ready for viral research)
  - Type B: Generic topics (suggests specific angles)
  - Type C: Trending topics (great for viral reels)
  - Type D: Ambiguous topics (needs clarification)
- **PDF/File Upload**: Upload PDFs or text files with proper content extraction (no word fragmentation)
- **RAG System**: 22 training scripts from Vibhay's viral content
- **Save/History**: Save scripts to localStorage, view and load from history
- **Skip Research Toggle**: Use only uploaded content without web research
- **Improved UI**: Clean script display with custom markdown styling

### Tech Stack
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11+
- **AI Models**:
  - Claude Sonnet 4 (script writing)
  - GPT-4o-mini (angle planning)
  - Perplexity Sonar Pro (research)
- **Database**: ChromaDB (vector storage)
- **API**: OpenRouter

### Key Files
```
backend/
├── app/
│   ├── agents/
│   │   ├── graph.py              # LangGraph workflow
│   │   ├── multi_angle_writer.py # 3-script generator
│   │   ├── research_orchestrator.py # Multi-stage research
│   │   ├── script_rag.py         # RAG from training data
│   │   └── prompts.py            # Script writing prompts
│   └── api/
│       └── server.py             # FastAPI endpoints
├── training_data/
│   └── vibhay_scripts.py         # 22 training scripts

frontend/
├── src/app/
│   ├── page.tsx                  # Main studio page
│   └── train/page.tsx            # Training interface
```

---

## Git Commands

### Pull Latest
```bash
git pull origin main
```

### Check Current Version
```bash
git log -1 --format="%h %s"
```

### View All Tags
```bash
git tag -l
```

---

## Upcoming: Version 2.0.0

*Features to be added...*

---

## Environment Setup

### Required Environment Variables (.env)
```
OPENAI_API_KEY=your_openrouter_api_key
```

### Install & Run
```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.api.server:server --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```
