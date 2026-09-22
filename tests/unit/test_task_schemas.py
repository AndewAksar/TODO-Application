from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from services.api_gateway.app.tasks.schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskUpdateRequest,
)

pytestmark = pytest.mark.unit


class TaskAttributeStub:
    def __init__(self) -> None:
        self.id = 42
        self.user_id = 7
        self.title = "Buy milk"
        self.description = "After work"
        self.is_done = True
        self.done_at = datetime(2026, 8, 18, 13, 0, tzinfo=UTC)
        self.due_at = datetime(2026, 8, 18, 12, 30, tzinfo=UTC)
        self.created_at = datetime(2026, 8, 17, 9, 0, tzinfo=UTC)
        self.updated_at = datetime(2026, 8, 18, 13, 0, tzinfo=UTC)


def test_create_accepts_title_only() -> None:
    payload = TaskCreateRequest(title="Buy milk")

    assert payload.title == "Buy milk"
    assert payload.description is None
    assert payload.due_at is None


def test_create_accepts_complete_payload_with_aware_due_at() -> None:
    due_at = datetime(2026, 8, 18, 12, 30, tzinfo=UTC)

    payload = TaskCreateRequest(
        title="Buy milk",
        description="After work",
        due_at=due_at,
    )

    assert payload.title == "Buy milk"
    assert payload.description == "After work"
    assert payload.due_at == due_at


def test_create_strips_title_whitespace() -> None:
    payload = TaskCreateRequest(title="  Buy milk  ")

    assert payload.title == "Buy milk"


def test_create_rejects_missing_title() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest.model_validate({})


def test_create_rejects_empty_title() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest(title="")


def test_create_rejects_whitespace_only_title() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest(title="     ")


def test_create_accepts_title_at_maximum_length() -> None:
    title = "M" * 255

    payload = TaskCreateRequest(title=title)

    assert payload.title == title


def test_create_rejects_title_over_maximum_length() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest(title="M" * 256)


def test_create_rejects_naive_due_at() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest(title="Buy milk", due_at=datetime(2026, 8, 18, 12, 0))


def test_create_rejects_user_id() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest.model_validate({"title": "Buy milk", "user_id": 999})


def test_create_rejects_client_supplied_completion_state() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest.model_validate({"title": "Buy milk", "is_done": True})


def test_empty_update_has_no_update_commands() -> None:
    payload = TaskUpdateRequest()

    assert payload.model_dump(exclude_unset=True) == {}


def test_omitted_update_description_is_not_emitted() -> None:
    payload = TaskUpdateRequest()

    assert "description" not in payload.model_dump(exclude_unset=True)


def test_update_preserves_explicit_null_description() -> None:
    payload = TaskUpdateRequest(description=None)

    assert payload.model_dump(exclude_unset=True) == {"description": None}


def test_update_preserves_explicit_null_due_at() -> None:
    payload = TaskUpdateRequest(due_at=None)

    assert payload.model_dump(exclude_unset=True) == {"due_at": None}


def test_update_preserves_explicit_false_completion_state() -> None:
    payload = TaskUpdateRequest(is_done=False)

    assert payload.model_dump(exclude_unset=True) == {"is_done": False}


def test_update_preserves_explicit_true_completion_state() -> None:
    payload = TaskUpdateRequest(is_done=True)

    assert payload.model_dump(exclude_unset=True) == {"is_done": True}


def test_update_rejects_explicit_null_title() -> None:
    with pytest.raises(ValidationError):
        TaskUpdateRequest(title=None)


def test_update_rejects_explicit_null_completion_state() -> None:
    with pytest.raises(ValidationError):
        TaskUpdateRequest(is_done=None)


def test_update_accepts_and_normalizes_meaningful_title() -> None:
    payload = TaskUpdateRequest(title="  Buy oat milk  ")

    assert payload.title == "Buy oat milk"


def test_update_rejects_whitespace_only_title() -> None:
    with pytest.raises(ValidationError):
        TaskUpdateRequest(title="   ")


def test_update_rejects_user_id() -> None:
    with pytest.raises(ValidationError):
        TaskUpdateRequest.model_validate({"user_id": 999})


def test_response_can_be_built_from_attributes() -> None:
    task = TaskAttributeStub()

    response = TaskResponse.model_validate(task)

    assert response.model_dump() == {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "is_done": task.is_done,
        "done_at": task.done_at,
        "due_at": task.due_at,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }
