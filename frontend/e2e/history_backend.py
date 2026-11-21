"""Owned loopback-only fictional backend for browser integration, not production."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import uvicorn
from api.main import create_app

if __name__ == "__main__":
    uvicorn.run(create_app({"mode": "synthetic_history", "history": {
        "as_of": "2026-11-20", "seed": 42017}}), host="127.0.0.1", port=8001, log_level="warning")
