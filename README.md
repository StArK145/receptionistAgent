# Voice Doctor Assistant

A local clinic appointment assistant with a React dashboard and a FastAPI voice backend. The backend uses Pipecat, WebRTC, ElevenLabs speech services, and OpenRouter for the LLM. Appointment data is stored in SQLite.

## Requirements

- Python 3.11 or newer
- Node.js 18 or newer and npm
- An OpenRouter API key
- An ElevenLabs API key and voice ID

## Setup

### 1. Configure environment variables

From the repository root, copy `.env.example` to `.env` and add your keys:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=google/gemini-2.5-flash
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_elevenlabs_voice_id
```

OpenRouter is the primary LLM provider. `GEMINI_API_KEY` and `GEMINI_MODEL` are optional fallback settings.

### 2. Install and run the backend

Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

On macOS or Linux, activate the environment with `source .venv/bin/activate`.

The backend initializes and seeds the SQLite database at startup. By default it uses `backend/doctor_assistant.db`. Set `DATABASE_PATH` in `.env` to choose another location.

- API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)
- Doctors and availability: `GET /api/doctors`
- Appointments: `GET /api/appointments`
- Live events: `GET /api/events` (Server-Sent Events)
- WebRTC signaling: `POST /api/offer`

### 3. Install and run the frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually [http://localhost:5173](http://localhost:5173). The frontend uses same-origin API paths by default. To point it to another backend, create `frontend/.env.local` with `VITE_API_URL=http://localhost:8000`.

## Useful commands

```powershell
# Frontend production build
cd frontend
npm run build

# From repository root: run backend tests (if present)
python -m pytest backend
```

## Project layout

```text
backend/       FastAPI application, Pipecat voice bot, appointment services, and SQLite access
frontend/      React + Vite dashboard and WebRTC client
.env.example  Template for local backend configuration
```

## Notes

- The browser needs microphone permission to place a voice call.
- The development server allows frontend requests from `localhost:5173` and `127.0.0.1:5173`.
- `backend/doctor_assistant.db` is local runtime data and is intentionally ignored by Git. Startup creates a fresh seeded database when needed.
