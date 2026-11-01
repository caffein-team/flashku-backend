from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers.auth_router import router as auth_router
from app.config import settings
from app.database.connection import get_connection
from app.database.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
)

# Enable CORS for Expo Go and cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router, prefix="/api")


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
