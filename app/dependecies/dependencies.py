import logging
from contextlib import asynccontextmanager

from fastapi import HTTPException, Depends
import psycopg2

from app.db import get_db_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", mode="a")
    ]
)


def get_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    return logger


def get_error_handler() -> callable:
    def handler(e: Exception, logger: logging.Logger):
        if isinstance(e, psycopg2.OperationalError):
            logger.error("Database operation failed: %s", e)
            raise HTTPException(status_code=500, detail="Database error")
        if isinstance(e, Exception):
            logger.error("Unhandled error: %s", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    return handler


class CoreDependencies:
    def __init__(
            self,
            db=Depends(get_db_connection),
            logger: logging.Logger = Depends(get_logger),
            error_handler: callable = Depends(get_error_handler),
    ):
        self.db = db
        self.logger = logger
        self.error_handler = error_handler


@asynccontextmanager
async def manage_db_connection(core_deps: CoreDependencies):
    try:
        yield core_deps.db
    finally:
        if core_deps.db:
            core_deps.db.close()
