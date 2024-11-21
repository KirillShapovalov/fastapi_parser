from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class RepoTop100Schema(BaseModel):
    repo: str
    owner: str
    position_cur: Optional[int]
    position_prev: Optional[int]
    stars: int
    watchers: int
    forks: int
    open_issues: int
    language: Optional[str]

    @classmethod
    def valid_sort_fields(cls):
        return list(cls.__fields__.keys())


class RepoActivitySchema(BaseModel):
    date: date
    commits: int
    authors: List[str]


class NoDataResponse(BaseModel):
    success: bool
    message: str
