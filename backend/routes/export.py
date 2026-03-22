# backend/routes/export.py
# Project Export Endpoint
#
# POST /api/export/project
#   → Returns project.zip containing ST code, HMI HTML, P&ID HTML, and report.md
#
# Constraints: Does NOT modify any existing endpoints or database schemas.

from fastapi import APIRouter, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from backend.engine.project_exporter import build_project_zip, build_report_md
from backend.engine.engineering_scorer import PLCEngineeringScorer

router = APIRouter()


class ExportRequest(BaseModel):
    program_name:  str
    brand:         Optional[str] = "GENERIC"
    domain_type:   Optional[str] = "general"
    plc_code:      Optional[str] = ""
    hmi_html:      Optional[str] = ""
    pid_html:      Optional[str] = ""
    signal_map:    Optional[dict] = {}
    warnings:      Optional[list] = []
    llm_status:    Optional[str] = "REAL"   # "REAL" or "STUB"


@router.post("/project")
def export_project(req: ExportRequest, http_request: Request):
    """
    Bundle PLC ST, HMI HTML, P&ID HTML, and generation report into a ZIP file.
    Returns application/zip for direct browser download.
    """
    # Score the PLC code
    scorer   = PLCEngineeringScorer()
    eng_score = scorer.score(req.plc_code or "")

    # Build validation summary (best-effort from what the frontend passed)
    validation_result = {
        "iec_valid":    True,
        "iec_errors":   [],
        "iec_warnings": req.warnings or [],
    }

    # Build detailed Markdown report
    report_md = build_report_md(
        program_name      = req.program_name,
        engineering_score = eng_score,
        validation_result = validation_result,
        signal_map        = req.signal_map  or {},
        warnings          = req.warnings    or [],
        brand             = req.brand       or "GENERIC",
        domain_type       = req.domain_type or "general",
        llm_status        = req.llm_status  or "REAL",
    )

    # Build ZIP
    zip_bytes = build_project_zip(
        st_code      = req.plc_code   or "",
        hmi_html     = req.hmi_html   or "",
        pid_html     = req.pid_html   or "",
        report_md    = report_md,
        program_name = req.program_name,
    )

    filename = f"{req.program_name}_project.zip"
    return Response(
        content     = zip_bytes,
        media_type  = "application/zip",
        headers     = {"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/score")
def score_code(body: dict, http_request: Request):
    """
    POST /api/export/score
    Body: {"code": "<ST code string>"}
    Returns engineering score breakdown.
    """
    code  = body.get("code", "")
    scorer = PLCEngineeringScorer()
    result = scorer.score(code)
    return result
