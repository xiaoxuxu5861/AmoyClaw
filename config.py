from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is optional at import time
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
COURSES_DIR = DATA_DIR / "courses"
OUTPUTS_DIR = DATA_DIR / "outputs"
DOCUMENTS_DIR = DATA_DIR / "documents"
DB_PATH = DATA_DIR / "amoyclaw.db"
SCHEMA_PATH = BASE_DIR / "memory" / "schema.sql"

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_AGENT_STEPS = 8

if load_dotenv:
    load_dotenv(BASE_DIR / ".env")

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "minimax")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-M3")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", MINIMAX_API_KEY)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", MINIMAX_BASE_URL)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", MINIMAX_MODEL)

MODEL_DISPLAY_NAME = os.getenv("MODEL_DISPLAY_NAME", "MiniMax-M3")
MODEL_STATUS_LABEL = os.getenv("MODEL_STATUS_LABEL", "MiniMax 在线")


def ensure_dirs() -> None:
    for path in (DATA_DIR, COURSES_DIR, OUTPUTS_DIR, DOCUMENTS_DIR):
        path.mkdir(parents=True, exist_ok=True)
