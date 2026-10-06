# Campus Customs — Homework 4

A React/Vite storefront with a FastAPI and PydanticAI Campus Concierge backend. The assistant uses `gpt-5.6-luna` through Portkey to give database-backed catalogue and inventory answers.

## What is included

- `frontend/` — Vite + React + TypeScript storefront
- `backend/` — FastAPI API and four-file agent implementation
- `output/` — harness notes, design/usability notes, audit trail, and browser-check evidence
- `AI_prompts.md` — chronological prompt log

## Add the local data pack

The supplied data is intentionally not included in Git. Before running the app, place the unzipped data pack here:

```text
hw4/
└── data/
    ├── campus_customs.db
    └── products/
```

## Configure the API key

Copy `.env.example` to `.env` in this `hw4/` folder and replace the placeholder with your own Portkey key. Do not commit `.env`.

```bash
cp .env.example .env
```

## Run the backend

Use Python 3.11+ and, from `hw4/`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

## Run the frontend

In a second terminal, from `hw4/frontend/`:

```bash
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend expects the API at `http://localhost:8000`.

## Verify

Ask the Campus Concierge a stock question, such as whether the Baseball Left Chest Crewneck is available in XS. The checked result, tool activity, and run stop event are recorded in `output/audit_trail.json`. For visual browser evidence, open `output/app_check.html`.
