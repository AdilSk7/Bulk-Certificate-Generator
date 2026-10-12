from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from . import models
from .database import engine, run_migrations
from .api import jobs
from .api import certificates

models.Base.metadata.create_all(bind=engine)
run_migrations(engine)

app = FastAPI(title="Bulk Certificate Generator")

# Build CORS securely matching strictly requested origins dynamically assigned
raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(certificates.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Static file serving for unified full-stack production deployment
frontend_dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if not os.path.exists(frontend_dist_dir):
    frontend_dist_dir = os.path.abspath(os.path.join(os.getcwd(), "frontend", "dist"))

if os.path.isdir(frontend_dist_dir):
    assets_dir = os.path.join(frontend_dist_dir, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Do not intercept API, documentation, or health check routes
        if (
            full_path.startswith("api/")
            or full_path == "api"
            or full_path in ("docs", "openapi.json", "health", "redoc")
        ):
            raise HTTPException(status_code=404, detail="Not Found")

        file_path = os.path.join(frontend_dist_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)

        index_file = os.path.join(frontend_dist_dir, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)

        raise HTTPException(status_code=404, detail="Not Found")
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "message": "Bulk Certificate Generator API is running",
            "docs": "/docs",
            "health": "/health"
        }
