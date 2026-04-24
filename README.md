# AI-First CRM HCP Interaction Logger

A production-structured demo CRM module where Healthcare Professional (HCP) interaction logging is controlled only by an AI assistant. The left panel renders a disabled CRM form; users update it exclusively through chat on the right.

## Architecture

- **Frontend:** React, Redux Toolkit, Tailwind CSS, Inter font.
- **Backend:** FastAPI, async SQLAlchemy, Alembic.
- **AI Layer:** LangGraph orchestrates tool selection and execution. Groq provides the LLM with `gemma2-9b-it` as primary and `llama-3.3-70b-versatile` as fallback.
- **Database:** PostgreSQL via Docker Compose.

Simple architecture diagram:

```text
User -> React UI -> FastAPI -> LangGraph Agent -> Tool -> PostgreSQL
  ^                                                       |
  |------------------- Response / Updated UI -------------|
```

LangGraph flow:

```text
START -> classify_intent -> tool_execution -> format_response -> END
```

The frontend never sends field patches directly from user input. It sends natural language to `/api/v1/chat`; the backend agent validates, normalizes, persists, and returns the canonical interaction state.

## LangGraph Agent Role

The LangGraph agent is the orchestration layer for the HCP interaction workflow.

Its role in this project is to:

- receive the user's natural-language CRM request
- inspect the current interaction state
- classify the intent of the request
- choose exactly one primary sales-related tool for that request
- execute the tool
- persist structured results through the backend service layer
- return the updated interaction state and assistant response to the UI

In practical terms, the LangGraph agent manages the full HCP interaction lifecycle for this module:

- creating/logging new HCP interactions
- editing previously logged interaction details
- summarizing the current interaction for CRM usage
- retrieving prior HCP interaction history
- recommending next-step follow-up actions for field representatives

Graph flow used in the implementation:

```text
START -> classify_intent -> tool_execution -> format_response -> END
```

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

## LangGraph Tools

This project defines five sales-focused LangGraph tools for HCP interaction management.

### 1. LogInteractionTool

Purpose:
- Capture a new HCP interaction from natural language entered in chat.

How it works:
- Uses the LLM to extract structured CRM fields such as HCP name, interaction type, date, time, sentiment, topics discussed, and materials shared.
- Supports summarization/entity-style extraction from free-form field rep notes.
- Normalizes outputs before persistence.
- Saves the interaction to the SQL database and returns the updated form state.

### 2. EditInteractionTool

Purpose:
- Modify an already logged HCP interaction.

How it works:
- Uses the current saved interaction plus the user's correction message.
- Updates only the fields explicitly mentioned by the user.
- Preserves untouched fields by performing a safe partial backend merge.
- Returns the updated interaction without replacing the entire object.

### 3. SummarizeInteractionTool

Purpose:
- Generate a concise CRM-ready summary of the current HCP interaction.

How it works:
- Reads the structured interaction state.
- Uses the LLM to create a concise summary suitable for CRM review or downstream usage.

### 4. FetchHCPHistoryTool

Purpose:
- Retrieve historical interactions for the same HCP.

How it works:
- Uses the HCP name from the current form or user request.
- Queries the database for prior interactions.
- Returns the history separately without overwriting the active interaction form.

### 5. SuggestNextActionTool

Purpose:
- Recommend practical next actions for sales/follow-up activity.

How it works:
- Uses the saved interaction context.
- Generates actionable follow-up suggestions for field reps.
- Persists those suggestions into `ai_suggested_followups`.
- Returns them to the UI as clickable quick actions.

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

Open `http://localhost:4010`.

## Demo Prompts

- `Today I met Dr. Sharma. Sentiment was positive. Shared brochure.`
- `Correction, sentiment was negative`
- `Give summary`
- `Show previous interactions with Dr. Sharma`
- `What should I do next?`

These prompts are enough for a reviewer to verify all five tools quickly.

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
- If the Groq API key is missing or the LLM call fails, the backend returns a friendly fallback response instead of a raw server error, and the UI shows that message in the chat panel.
