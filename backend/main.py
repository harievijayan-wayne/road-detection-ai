import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from backend.app.config import settings
from backend.app.database import engine, Base
from backend.api import detect, damages, inspections, map as map_api, reports, analytics
from backend.services.seed_data import generate_sample_road_images, seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables, generate sample images and seed realistic data
    Base.metadata.create_all(bind=engine)
    generate_sample_road_images()
    seed_database()
    print("[RoadDamageAI] Backend engine initialized and seeded successfully.")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent Road Damage Detection, Segmentation, Severity & GIS Prioritization Platform",
    lifespan=lifespan
)

# CORS Middleware (supports local development and frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories for uploaded images/videos and demo samples
app.mount("/api/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/api/samples", StaticFiles(directory=settings.SAMPLE_DATA_DIR), name="samples")

# Include Routers
app.include_router(detect.router, prefix=settings.API_V1_STR)
app.include_router(damages.router, prefix=settings.API_V1_STR)
app.include_router(inspections.router, prefix=settings.API_V1_STR)
app.include_router(map_api.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "device": settings.DEVICE,
        "demo_mode": True
    }

@app.get("/api/demo-samples")
def list_demo_samples():
    """Returns available sample road images for one-click testing in the frontend."""
    samples = []
    if os.path.exists(settings.SAMPLE_DATA_DIR):
        for fname in os.listdir(settings.SAMPLE_DATA_DIR):
            if fname.lower().endswith((".jpg", ".png", ".jpeg")):
                samples.append({
                    "filename": fname,
                    "title": fname.replace("sample_", "").replace(".jpg", "").replace("_", " ").title(),
                    "url": f"/api/samples/{fname}"
                })
    return {"samples": samples}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
