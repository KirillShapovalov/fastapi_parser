from typing import List, Union

from fastapi import APIRouter, Depends, Query, Path

from app.core.utils import DateRangeParams, SortFields, SortOrder
from app.core.decorators import router_error_handler
from app.crud import get_top100_repos, get_repo_activity
from app.dependecies import CoreDependencies, manage_db_connection
from app.schemas import RepoTop100Schema, RepoActivitySchema, NoDataResponse

router = APIRouter()


@router.get("/top100", response_model=Union[List[RepoTop100Schema], NoDataResponse])
@router_error_handler
async def read_top100_repos(
        sort_by: SortFields | None = Query(None, description="Поле для сортировки"),
        order: SortOrder = Query("asc", description="Порядок сортировки"),
        core_deps: CoreDependencies = Depends(CoreDependencies)
):
    async with manage_db_connection(core_deps) as db:
        repos = await get_top100_repos(db, logger=core_deps.logger, sort_by=sort_by, order=order)
        if not repos:
            core_deps.logger.info("No repositories found in the database.")
            return NoDataResponse(
                success=False,
                message="No repositories found in the database."
            )
        core_deps.logger.debug("Successfully fetched top 100 repos.")
        return repos


@router.get("/{owner}/{repo}/activity", response_model=Union[List[RepoActivitySchema], NoDataResponse])
@router_error_handler
async def read_repo_activity(
        owner: str = Path(..., description="Автор репозитория"),
        repo: str = Path(..., description="Название репозитория"),
        date_params: DateRangeParams = Depends(DateRangeParams.as_form),
        core_deps: CoreDependencies = Depends(CoreDependencies)
):
    async with manage_db_connection(core_deps) as db:
        activity = await get_repo_activity(db, owner, repo, date_params.since, date_params.until,
                                           logger=core_deps.logger)
        if not activity:
            core_deps.logger.info("No activity found for repository %s/%s in the given date range.", owner, repo)
            return NoDataResponse(
                success=False,
                message=f"No activity found for repository {owner}/{repo} in the given date range."
            )
        core_deps.logger.info("Successfully fetched activity for repo %s/%s.", owner, repo)
        return activity
