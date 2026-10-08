from fastapi import FastAPI
from . import models
from .database import engine
from .api import jobs
from .api import certificates

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bulk Certificate Generator")

app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(certificates.router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "ok"}
