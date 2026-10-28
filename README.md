# AetherMind — AI Task and Goal Manager

CA3 Mini Project 2 — Generative AI Foundations (CSB312)

AetherMind converts natural-language task descriptions into a validated structured preview using Gemini. The user reviews the fields and explicitly confirms before the task is saved to SQLite.

## Features

- Natural-language text input
- Gemini structured JSON extraction
- Pydantic schema validation, including ISO date checks
- Review-before-save flow
- SQLite persistence
- Task dashboard with counts, filters, status updates, and delete
- User-facing error handling
- FastAPI API documentation at `/docs`
- Single FastAPI service serves frontend and API, simplifying deployment

## Architecture

`Browser UI → POST /api/extract → Gemini → Pydantic validation → preview → user confirms → POST /api/tasks → SQLite → dashboard`

The extraction endpoint does **not** save anything. Saving happens only after user confirmation.

## Requirements

- Python 3.10+
- A Gemini API key from Google AI Studio
- Internet connection for Gemini requests

## Run locally on macOS

1. Open Terminal and move into this project directory.
2. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create your environment file:

   ```bash
   cp .env.example .env
   ```

5. Edit `.env` and replace `your_gemini_api_key_here` with your own Gemini API key. Do not share or commit this file.

6. Start the server from the project root:

   ```bash
   uvicorn app.main:app --reload
   ```

7. Open <http://127.0.0.1:8000>. API docs: <http://127.0.0.1:8000/docs>.

The SQLite database `aethermind.db` is created automatically on first start.

## Test checklist

1. **Successful extraction and save:** enter “Finish my Python assignment by 2026-11-05. High priority.” Review the result and click Confirm & save. Verify it appears in the task list.
2. **No deadline:** enter a task without a deadline. The deadline should remain blank instead of being invented.
3. **Short input:** submit fewer than 8 characters. The UI should reject it.
4. **Gemini key missing/invalid:** remove or invalidate the key and try extraction. A clear error should appear; no task should be saved.
5. **Status update:** change a task to In Progress or Completed and refresh the page.
6. **Delete:** delete a task and confirm it disappears.
7. **Persistence:** refresh the page and verify saved tasks remain.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/extract` | Extract structured task preview; does not save |
| POST | `/api/tasks` | Validate and save a task |
| GET | `/api/tasks` | List saved tasks |
| PATCH | `/api/tasks/{id}` | Update task status |
| DELETE | `/api/tasks/{id}` | Delete a task |

## Schema

- `title`: string, 3–160 characters
- `description`: string, up to 1,000 characters
- `deadline`: `YYYY-MM-DD` or `null`
- `priority`: `Low`, `Medium`, or `High`
- `category`: string, 2–60 characters
- Database fields additionally include `id`, `status`, and `created_at`

## Deployment notes

Deploy this as a Python web service on a host that supports FastAPI/ASGI. Configure `GEMINI_API_KEY` and `GEMINI_MODEL` as service environment variables. Do not upload `.env` to the hosting platform or source control.

**Important:** SQLite is suitable for a small academic demo, but the database file must live on persistent storage. If the hosting provider has an ephemeral filesystem, tasks may disappear after restarts/redeployments. Use a persistent disk or a managed database for a reliable public deployment. Set `DATABASE_PATH` to the persistent disk path when needed.

The frontend is served by FastAPI, so the deployed frontend URL and backend API share the same origin. Submit that frontend URL in the assessment.

## Report outline

1. Project title and objective
2. Problem statement and selected automation
3. Technology stack
4. Architecture and workflow diagram
5. Prompt design and schema
6. Validation and database design
7. API endpoints
8. Screenshots and test evidence
9. Deployment URL
10. Limitations and future scope
11. Conclusion

## Limitations and future scope

- Text input only in the first version; audio/document input is not implemented.
- Gemini responses depend on API availability and the selected model.
- SQLite is intended for this small project, not high-concurrency production use.
- Authentication and multi-user accounts are not included.
- Relative dates can be ambiguous; always review extracted fields before saving.
