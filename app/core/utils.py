from datetime import date
from enum import Enum

from pydantic import BaseModel, validator, Field
from fastapi import HTTPException, Query

from app.schemas import RepoTop100Schema


class DateRangeParams(BaseModel):
    since: date
    until: date

    @validator("until")
    def validate_date_range(cls, until, values):
        since = values.get("since")
        if since and since > until:
            raise HTTPException(
                status_code=422,
                detail="Invalid date range: 'since' must be earlier than or equal to 'until'."
            )
        return until

    @classmethod
    def as_form(cls,
                since: date = Query(..., description="Дата начала выборки в формате YYYY-MM-DD"),
                until: date = Query(..., description="Дата окончания выборки в формате YYYY-MM-DD")
                ):
        return cls(since=since, until=until)


def generate_sort_fields_enum():
    return Enum('SortFields', {field: field for field in RepoTop100Schema.valid_sort_fields()})


SortFields = generate_sort_fields_enum()


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"
