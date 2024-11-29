from fastapi import FastAPI, Depends

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


app.include_router(repos.router, prefix="/api/repos", tags=["repos"])
