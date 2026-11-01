import psycopg
from psycopg.rows import dict_row
from app.config import settings


def get_connection():
    return psycopg.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        row_factory=dict_row
    )
