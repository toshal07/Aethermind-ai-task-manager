import pytest
from pydantic import ValidationError
from app.schemas import TaskCreate


def test_valid_task():
    task = TaskCreate(
        title="Finish Python assignment",
        description="Complete the notebook",
        deadline="2026-11-05",
        priority="High",
        category="Study",
    )
    assert task.title == "Finish Python assignment"
    assert task.deadline == "2026-11-05"


def test_invalid_date_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="Finish assignment", deadline="next Friday", priority="Medium", category="Study")


def test_invalid_priority_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="Finish assignment", deadline=None, priority="Urgent", category="Study")


def test_blank_title_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(title="   ", deadline=None, priority="Medium", category="Study")
