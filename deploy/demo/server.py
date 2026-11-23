"""Synthetic-only demo composition; no alternative readiness implementation."""
import os
from pathlib import Path
import uvicorn
from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from api.main import create_app

app = create_app({"mode": "synthetic_history", "history": {"as_of": "2026-11-20", "seed": 42017}})
# Default API documentation loads external CDN assets; omit it in this demo only.
app.router.routes[:] = [r for r in app.router.routes if getattr(r, "path", None) not in
    {"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}]
assets = Path("/app/frontend/dist")
app.mount("/assets", StaticFiles(directory=assets / "assets"), name="assets")

@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    # Fixed UI entry points only. Unknown API/files/debug paths stay 404.
    if path not in ("", "dashboard"):
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(assets / "index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "10000")), workers=1,
                access_log=False, log_level="info", timeout_graceful_shutdown=30)
