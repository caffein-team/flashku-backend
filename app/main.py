from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routers.auth_router import router as auth_router
from app.api.routers.user_router import router as user_router
from app.config import settings
from app.database.connection import get_connection
from app.database.init_db import init_db

# Ensure uploads directory exists
UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
)

# Enable CORS for Expo Go, browsers, and cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded static files with access from any origin
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "Welcome to My API",
        "version": settings.APP_VERSION
    }


@app.get("/health/database")
def database_health():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()

        return {
            "database": "connected"
        }

    except Exception as e:
        return {
            "database": "disconnected",
            "message": str(e)
        }
