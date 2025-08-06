import os
import subprocess
import sys
from unittest.mock import patch

import pytest


def test_app_starts_minimal(monkeypatch):
    """Smoke test: app.py should start without crashing (integration points mocked)."""
    # Patch environment to avoid real integration
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("JIRA_INSTANCE_URL", "http://localhost")
    monkeypatch.setenv("JIRA_USERNAME", "test")
    monkeypatch.setenv("JIRA_API_TOKEN", "test")
    monkeypatch.setenv("JIRA_CLOUD", "true")

    # Patch sys.argv to avoid issues
    monkeypatch.setattr(sys, "argv", ["app.py"])

    # Run the app in a subprocess, but exit after import
    # Mock py2neo import to avoid database dependency
    code = (
        "import sys; sys.path.insert(0, '.'); "
        "import types; "
        "sys.modules['py2neo'] = types.ModuleType('py2neo'); "
        "sys.modules['py2neo'].Graph = type('Graph', (), {}); "
        "import app; print('APP_STARTUP_OK')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=10
    )

    assert "APP_STARTUP_OK" in result.stdout
    assert result.returncode == 0
