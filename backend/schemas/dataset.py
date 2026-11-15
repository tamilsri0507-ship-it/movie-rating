"""Pydantic schemas for dataset validation and duplicate detection."""

from typing import List, Optional
from pydantic import BaseModel


class ValidationIssue(BaseModel):
    record_id: Optional[int]
    rank: Optional[int]
    title: str
    issue_type: str
    description: str


class DatasetValidationResponse(BaseModel):
    status: str = "success"
    is_valid: bool
    total_records: int
    issue_count: int
    issues: List[ValidationIssue]
    health_score: float


class DuplicateItem(BaseModel):
    title: str
    count: int
    ids: List[int]
    ranks: List[int]


class DatasetDuplicatesResponse(BaseModel):
    status: str = "success"
    has_duplicates: bool
    duplicate_groups_count: int
    total_duplicate_rows: int
    duplicates: List[DuplicateItem]
