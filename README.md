# ScriptAI Pro

AI-powered viral Instagram Reels script generator for Indian tech audiences.

## Tech Stack

- **Frontend**: Next.js 14 + Tailwind CSS
- **Backend**: FastAPI + LangGraph
- **LLMs**: Claude 3.5 Sonnet (writing) + Perplexity sonar-pro (research) + GPT-4o-mini (analysis)
- **Vector DB**: ChromaDB (local, for style training)
- **API Gateway**: OpenRouter (unified LLM access)

## Features

- Deep investigative research via Perplexity
- Viral hook generation (5 variants per script)
- Multi-hook analysis with scoring
- Style learning from trained scripts
- Real-time streaming output
- India-focused content localization

## Local Development

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Add your OpenRouter API key to .env
uvicorn app.api.server:server --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Deployment

### Backend (Render)

1. Create a new Web Service on Render
2. Connect your GitHub repo
3. Set Root Directory: `backend`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `uvicorn app.api.server:server --host 0.0.0.0 --port $PORT`
6. Add Environment Variable: `OPENAI_API_KEY` (your OpenRouter key)

### Frontend (Vercel)

1. Import project on Vercel
2. Set Root Directory: `frontend`
3. Add Environment Variable: `NEXT_PUBLIC_API_URL` (your Render backend URL)

## Environment Variables

### Backend (.env)
```
OPENAI_API_KEY=sk-or-your-openrouter-key
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Endpoints

- `GET /` - Health check
- `POST /train_script` - Train on a script example
- `POST /generate_stream` - Generate script (streaming)

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph nodes & prompts
│   │   ├── api/             # FastAPI server
│   │   ├── db/              # ChromaDB storage
│   │   ├── schemas/         # Pydantic models
│   │   └── utils/           # Helpers
│   └── requirements.txt
├── frontend/
│   ├── src/app/             # Next.js pages
│   └── package.json
└── README.md
```
