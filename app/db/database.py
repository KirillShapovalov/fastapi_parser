import os
import logging

from fastapi import Request
from psycopg2.pool import SimpleConnectionPool
from psycopg2 import OperationalError

logger = logging.getLogger(__name__)

# настройки PostgreSQL
DATABASE_CONFIG = {
    "host": os.getenv("PG_HOST"),
    "port": os.getenv("PG_PORT"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "database": os.getenv("PG_DB"),
}

# инициализация пула соединений
def init_db_pool():
    try:
        db_pool = SimpleConnectionPool(minconn=1, maxconn=5, **DATABASE_CONFIG)
        logger.info("Database connection pool created successfully.")
        return db_pool
    except OperationalError as e:
        logger.critical("Error creating database connection pool: %s", e)
        raise SystemExit("Failed to initialize database connection pool. Application exiting.")


async def get_db_connection(request: Request):
    db_pool = request.app.state.db_pool
    if not db_pool:
        raise RuntimeError("Database connection pool is not initialized.")
    conn = None
    try:
        conn = db_pool.getconn()
        yield conn
    except OperationalError as e:
        logger.error(f"Error getting database connection: {e}")
        raise
    finally:
        if conn:
            db_pool.putconn(conn)
