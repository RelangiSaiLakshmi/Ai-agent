"""Central configuration.

Reads settings from environment variables (optionally from a local `.env`
file). Uses a tiny built-in .env parser so the Milestone 1 scaffold runs with
zero third-party dependencies. In later milestones you may switch to
python-dotenv / pydantic-settings.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader: `KEY=value` lines, `#` comments. No dependencies."""
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        # Do not override variables already set in the real environment.
        os.environ.setdefault(key, value)


_load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class Settings:
    llm_provider: str = os.environ.get("LLM_PROVIDER", "mock")
    llm_model: str = os.environ.get("LLM_MODEL", "claude-sonnet-4-6")
    anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    db_path: str = os.environ.get("DB_PATH", str(PROJECT_ROOT / "data" / "app.db"))
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")

    def resolved_db_path(self) -> Path:
        p = Path(self.db_path)
        return p if p.is_absolute() else (PROJECT_ROOT / p)


# Mutable singleton — tests may override attributes (e.g. settings.db_path).
settings = Settings()
