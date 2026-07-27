from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

PasswordStr = Annotated[str, StringConstraints(min_length=8, max_length=128, strip_whitespace=True)]


class AuthSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegisterRequest(AuthSchema):
    email: EmailStr
    password: PasswordStr


class LoginRequest(AuthSchema):
    email: EmailStr
    password: PasswordStr


class TokenResponse(AuthSchema):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class UserResponse(AuthSchema):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: int
    email: EmailStr
    username: str | None = None
    created_at: datetime
