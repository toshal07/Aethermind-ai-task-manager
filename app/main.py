from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.ai_service import extract_task, AIServiceError
from app.config import APP_NAME
from app.database import init_db, create_task, list_tasks, update_task_status, delete_task
from app.schemas import ExtractRequest, TaskCreate, TaskRecord, TaskUpdate

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=f"{APP_NAME} API",
    description="Schema-guided AI task extraction and task management for the CSB312 CA3 mini project.",
    version="1.0.0",
    lifespan=lifespan,
)

# The frontend is served by this same app, so CORS is not required for normal use.
# This middleware also supports local testing from a separate frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": APP_NAME}


@app.post("/api/extract", response_model=TaskRecord | dict)
def extract(request: ExtractRequest):
    text = request.text.strip()
    if len(text) < 8:
        raise HTTPException(status_code=422, detail="Please describe your task in at least 8 characters.")
    try:
        task = extract_task(text)
        # Do not save here: return a preview so the user can review it first.
        return {"preview": task.model_dump(), "message": "Review the extracted fields, then confirm to save."}
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/tasks", response_model=dict, status_code=status.HTTP_201_CREATED)
def save_task(task: TaskCreate):
    try:
        saved = create_task(task.model_dump())
        return {"message": "Task saved successfully.", "task": saved}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="The task could not be saved. Please try again.") from exc


@app.get("/api/tasks", response_model=list[dict])
def get_tasks():
    return list_tasks()


@app.patch("/api/tasks/{task_id}", response_model=dict)
def change_task_status(task_id: int, update: TaskUpdate):
    updated = update_task_status(task_id, update.status)
    if updated is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"message": "Task status updated.", "task": updated}


@app.delete("/api/tasks/{task_id}")
def remove_task(task_id: int):
    if not delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"message": "Task deleted."}
