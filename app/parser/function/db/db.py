import os

import asyncpg

from function.utils import logger

# получение переменных окружения
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_DB = os.getenv("PG_DB")


async def init_db_pool():
    try:
        db_pool = await asyncpg.create_pool(
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DB,
            host=PG_HOST,
            port=PG_PORT,
            min_size=1,
            max_size=10,
            timeout=10
        )
        if not db_pool:
            raise RuntimeError("Database connection pool was not initialized correctly.")
        logger.info("Database connection pool initialized.")
        return db_pool
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise


async def close_db_pool(db_pool):
    if db_pool is not None:
        await db_pool.close()
        logger.info("Database connection pool closed.")
