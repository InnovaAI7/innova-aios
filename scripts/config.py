"""
DataOS — Configuration Loader

Reads credentials from .env file in workspace root.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = WORKSPACE_ROOT / ".env"

load_dotenv(ENV_PATH)


def get_env(key, required=True):
    value = os.getenv(key, "").strip()
    if not value:
        return None
    return value
