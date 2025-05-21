from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import tasks, plans
from datetime import datetime

app = FastAPI(
    title="Bluelabel Agent OS API",
    description="API for managing agents and tasks in the Bluelabel Agent OS",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router)
app.include_router(plans.router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    } 