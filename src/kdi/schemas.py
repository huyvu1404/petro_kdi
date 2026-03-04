from pydantic import BaseModel
from typing import List, Optional


class ReportRequest(BaseModel):
    report_type: str  # "daily" | "weekly"
    topic: str
    files: List[str]
    last_week_files: Optional[List[str]] = None


class ExcelFileResponse(BaseModel):
    filename: str
    content_base64: str


class ReportResponse(BaseModel):
    html_report_base64: str
    excel_files: List[ExcelFileResponse]
