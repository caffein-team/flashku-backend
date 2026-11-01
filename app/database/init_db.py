import logging
from app.database.connection import get_connection
from app.database.queries.user_queries import CREATE_USERS_TABLE

logger = logging.getLogger(__name__)


def init_db():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_USERS_TABLE)
            conn.commit()
            logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e


if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")
