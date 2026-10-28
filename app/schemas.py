from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


Priority = Literal["Low", "Medium", "High"]
TaskStatus = Literal["Pending", "In Progress", "Completed"]


class TaskExtraction(BaseModel):
    """Structured result returned by the AI before the user confirms saving."""
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=160)
    description: str = Field(default="", max_length=1000)
    deadline: Optional[str] = Field(
        default=None,
        description="Deadline as YYYY-MM-DD, or null if the user did not provide one."
    )
    priority: Priority = "Medium"
    category: str = Field(default="Personal", min_length=2, max_length=60)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Task title cannot be blank.")
        return value

    @field_validator("deadline")
    @classmethod
    def deadline_is_iso_date(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Deadline must be a valid date in YYYY-MM-DD format.") from exc
        return value

    @field_validator("category")
    @classmethod
    def category_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return "Personal"
        return value


class ExtractRequest(BaseModel):
    text: str = Field(min_length=8, max_length=5000)


class TaskCreate(TaskExtraction):
    pass


class TaskUpdate(BaseModel):
    status: TaskStatus


class TaskRecord(TaskExtraction):
    id: int
    status: TaskStatus
    created_at: str
