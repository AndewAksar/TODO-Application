import sys

import pytest
from services.api_gateway.app import db
from services.api_gateway.app.security import jwt
from services.api_gateway.app.settings import settings

pytestmark = pytest.mark.unit


def test_settings_loaded_from_single_canonical_module() -> None:
    assert "services.api_gateway.app.settings" in sys.modules
    assert "app.settings" not in sys.modules


def test_db_and_jwt_use_same_settings_object() -> None:
    assert db.settings is settings
    assert jwt.settings is settings
