from fastapi import FastAPI
from app.config import settings
from app.database.connection import get_connection

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.APP_DEBUG
)


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
            "message" : e
        }