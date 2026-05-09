# Build a Base

Build a Base is a React + Vite and FastAPI beauty assistant that helps users create cosmetic base routines with product compatibility checks, an AI Beauty Agent, saved routines, and a SQLite product database.

## Features

- AI Beauty Agent at `/api/agent`
- Live Google Shopping product search via SerpApi when `SERPAPI_API_KEY` is configured
- Base routine builder
- Skin type quiz
- Routine generator
- Makeup problem solver
- Makeup look recreator
- Saved results backed by SQLite
- Cosmetic-only safety guardrails and a disclaimer in every AI response

## Setup

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Add your OpenAI key to `.env`:

```bash
OPENAI_API_KEY=sk-...
```

Optional, for live product cards with current-ish prices and thumbnails:

```bash
SERPAPI_API_KEY=your_serpapi_key
```

3. Run with Docker:

```bash
docker compose up --build
```

4. Open the app:

- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## API

`POST /api/agent`

Send a goal, text input, optional image as a base64 string or URL, and an optional profile.

```json
{
  "goal": "Build a base routine",
  "text_input": "I have a selfie, quiz answers, oily T-zone, and want budget products.",
  "image": "data:image/jpeg;base64,...",
  "profile": {
    "preference": "natural finish",
    "budget": "drugstore",
    "quiz_answers": {
      "after_washing": "tight cheeks, shiny T-zone"
    }
  }
}
```

The backend agent chooses tools, combines their outputs, and returns a structured response with recommendations, follow-up questions when required, and a cosmetic-only disclaimer.

Product endpoints:

- `GET /products` or `GET /api/products`
- `GET /products/{id}` or `GET /api/products/{id}`
- `POST /recommend` or `POST /api/recommend`

`POST /recommend` compares the user's profile against products stored in SQLite. When `OPENAI_API_KEY` is configured, OpenAI chooses from the database candidates and explains the selections; otherwise Build a Base uses a deterministic score.

## Safety

Build a Base provides cosmetic and beauty recommendations only. It does not diagnose, treat, or advise on medical skin conditions. Users should consult a licensed medical professional for symptoms such as pain, spreading rash, bleeding, infection, severe irritation, or persistent skin changes.
