"""
SkillBridge Attendance Management API
Role-based REST API for attendance tracking with JWT authentication
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.database import engine, Base, get_db
from src.routes import auth, batches, sessions, attendance, monitoring
from src.config import settings
from seed import seed_database

# Create database tables on startup
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("SkillBridge API starting up...")
    yield
    # Shutdown
    print("SkillBridge API shutting down...")

app = FastAPI(
    title="SkillBridge Attendance API",
    description="Role-based attendance management system for SkillBridge",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(batches.router, prefix="/batches", tags=["Batches"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
app.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
app.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])

@app.post("/seed", tags=["Internal"])
async def trigger_seed():
    """
    Trigger database seeding with test data.
    Only works if the database is currently empty.
    """
    seed_database()
    return {"message": "Database seeding triggered. Check logs for details."}

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "SkillBridge Attendance API",
        "version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """API health endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
