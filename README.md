# AI-First CRM HCP Interaction Logger

A production-structured demo CRM module where Healthcare Professional (HCP) interaction logging is controlled only by an AI assistant. The left panel renders a disabled CRM form; users update it exclusively through chat on the right.

## Architecture

- **Frontend:** React, Redux Toolkit, Tailwind CSS, Inter font.
- **Backend:** FastAPI, async SQLAlchemy, Alembic.
- **AI Layer:** LangGraph orchestrates tool selection and execution. Groq provides the LLM with `gemma2-9b-it` as primary and `llama-3.3-70b-versatile` as fallback.
- **Database:** PostgreSQL via Docker Compose.

LangGraph flow:

```text
START -> classify_intent -> tool_execution -> format_response -> END
```

The frontend never sends field patches directly from user input. It sends natural language to `/api/v1/chat`; the backend agent validates, normalizes, persists, and returns the canonical interaction state.

## Features

- Read-only CRM form styled as real inputs/selects/textareas/radios.
- AI chat for logging, editing, summarizing, history lookup, and next-action suggestions.
- Five LangGraph tools:
  - `LogInteractionTool`
  - `EditInteractionTool`
  - `SummarizeInteractionTool`
  - `FetchHCPHistoryTool`
  - `SuggestNextActionTool`
- Confidence scores for AI decisions.
- Retry policy for invalid LLM JSON: same model once, fallback model once, then graceful failure.
- Structured logs for AI decisions, raw output, validated output, and DB results.
- Field highlight flash for updated fields.
- Demo seed data for Dr. Sharma history.

## Setup

### 1. Environment

Copy `.env.example` to `.env` and set `GROQ_API_KEY`.

```bash
cp .env.example .env
```

### 2. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 3. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8011
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Demo Prompts

- `Today I met Dr. Sharma. Sentiment was positive. Shared brochure.`
- `Correction, sentiment was negative`
- `Give summary`
- `Show previous interactions with Dr. Sharma`
- `What should I do next?`

## API

### `POST /api/v1/chat`

```json
{
  "message": "Today I met Dr. Sharma. Sentiment was positive. Shared brochure.",
  "interaction_id": null
}
```

Returns the canonical interaction, assistant message, tool name, tool explanation, confidence, changed fields, tool output, and optional history.

### `POST /api/v1/interaction`

Creates an empty draft interaction.

### `GET /api/v1/interaction/{id}`

Returns an interaction and its chat history.

### `PATCH /api/v1/interaction/{id}`

Backend-safe partial patch endpoint. The UI does not expose manual field editing.

## Production Notes

- Secrets are loaded from environment variables.
- LLM output is never trusted directly; it is parsed, validated, normalized, and merged server-side.
- `EditInteractionTool` returns only changed fields, and untouched values are preserved.
- History responses are separate from current form state and never overwrite the active interaction.
