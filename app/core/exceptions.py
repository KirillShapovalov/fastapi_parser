from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import psycopg2

from app.dependecies import get_logger

logger = get_logger()


async def db_connection_error_handler(request: Request, exc: psycopg2.OperationalError):
    logger.error("Database connection error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Failed to connect to the database. Please try again later."},
    )


async def sql_query_error_handler(request: Request, exc: psycopg2.ProgrammingError):
    logger.error("SQL query error: %s", exc)
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid SQL query. Check your inputs or sorting parameters."},
    )


async def generic_error_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please contact support."},
    )
