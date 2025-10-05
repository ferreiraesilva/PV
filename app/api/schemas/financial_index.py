from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class IndexValueInput(BaseModel):
    reference_date: date = Field(..., alias="referenceDate")
    value: float = Field(...)

    model_config = ConfigDict(populate_by_name=True)


class IndexValueBatchInput(BaseModel):
    values: list[IndexValueInput] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def _ensure_values(self) -> "IndexValueBatchInput":
        if not self.values:
            raise ValueError("At least one index value must be provided")
        return self


class IndexValueOutput(BaseModel):
    reference_date: date = Field(..., alias="referenceDate")
    value: float
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
