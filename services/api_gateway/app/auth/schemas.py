from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

NonEmptyPassword = Annotated[str, StringConstraints(min_length=1)]


class AuthSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegisterRequest(AuthSchema):
    email: EmailStr
    password: NonEmptyPassword


class LoginRequest(AuthSchema):
    email: EmailStr
    password: NonEmptyPassword


class TokenResponse(AuthSchema):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class UserResponse(AuthSchema):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    email: EmailStr
    username: str | None = None
    created_at: datetime
