from fastapi import FastAPI, Depends

from app.api.routers import repos

app = FastAPI()

app.include_router(repos.router, prefix="/api/repos", tags=["repos"])
