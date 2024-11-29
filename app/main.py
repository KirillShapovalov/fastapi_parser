from fastapi import FastAPI, Depends
from psycopg2 import OperationalError, ProgrammingError

from app.core.exceptions import (
    db_connection_error_handler,
    sql_query_error_handler,
    generic_error_handler,
)
from app.api.routers import repos
from app.db import init_db_pool

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    app.state.db_pool = init_db_pool()


@app.on_event("shutdown")
async def shutdown_event():
    if app.state.db_pool:
        app.state.db_pool.closeall()


# регистрация роутов
app.include_router(repos.router, prefix="/api/repos", tags=["repos"])

# регистрация обработчиков
app.add_exception_handler(OperationalError, db_connection_error_handler)
app.add_exception_handler(ProgrammingError, sql_query_error_handler)
app.add_exception_handler(Exception, generic_error_handler)
