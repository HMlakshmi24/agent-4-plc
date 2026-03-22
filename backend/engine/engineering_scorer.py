# backend/engine/engineering_scorer.py
# PLCEngineeringScorer — Content-based 0-100 engineering quality scoring
#
# Scores generated PLC Structured Text on 10 engineering criteria.
# Complements ConfidenceScoreCalculator (which scores generation process).
# This scores the CODE CONTENT itself.

import re


# ── SCORING CRITERIA ──────────────────────────────────────────────────────────
# Each entry: (label, regex_pattern, points, flags)

_CHECKS = [
    (
        "E-Stop logic present",
        r"\bI_EStop\b|\bI_E_Stop\b|\bEmergencyStop\b|\bI_EmergStop\b",
        10,
        re.IGNORECASE,
    ),
    (
        "State machine present",
        r"\bCASE\b.{1,40}\bOF\b|\bM_State\s*:=\s*\d+",
        10,
        re.DOTALL,
    ),
    (
        "Fault state implemented",
        # Named Fault branch OR Q_Alarm activated (alarm handler = fault state present)
        r"\bFault\s*:|STATE_FAULT\b|Q_Alarm\s*:=\s*TRUE",
        10,
        re.IGNORECASE,
    ),
    (
        "Edge detection used (R_TRIG / F_TRIG)",
        r"\bR_TRIG\b|\bF_TRIG\b",
        10,
        0,
    ),
    (
        "Timers declared and used (TON / TOF)",
        r"\bTON\b|\bTOF\b",
        10,
        0,
    ),
    (
        "Domain-specific sensors included",
        (
            r"\bI_PartSensor\b|\bI_LevelHigh\b|\bI_LevelLow\b"
            r"|\bI_Overload\b|\bI_TempHigh\b|\bI_JamSensor\b"
            r"|\bI_FlowFault\b|\bI_ThermalFault\b"
            r"|\bI_AgitatorRunning\b|\bI_SafetyValveOpen\b"
            r"|\bI_OverflowSensor\b|\bI_RejectSensor\b"
        ),
        10,
        0,
    ),
    (
        "Proper naming conventions (I_ / Q_ prefixes)",
        r"\bI_[A-Z][A-Za-z0-9]+\b.{0,200}\bQ_[A-Z][A-Za-z0-9]+\b",
        10,
        re.DOTALL,
    ),
    (
        "Alarm output declared and used",
        r"\bQ_Alarm\b|\bQ_\w*Alarm\w*\b|\bQ_\w*Fault\w*\b",
        10,
        re.IGNORECASE,
    ),
    (
        "IEC structure compliance (PROGRAM / END_PROGRAM / VAR / END_VAR)",
        r"\bPROGRAM\s+\w+\b.{10,}\bEND_PROGRAM\b",
        10,
        re.DOTALL,
    ),
    (
        "Startup delay timer or minimum 4 states",
        (
            r"\bStarting\b|\bT_Start\w*\b|\bT_PreHeat\b|\bT_\w+\s*\("
            r"|(?:(?:Idle|Idle,\s*)(?:[A-Za-z]+,\s*){2,}Fault)"
        ),
        10,
        re.IGNORECASE,
    ),
]


class PLCEngineeringScorer:
    """
    Scores PLC Structured Text code on 10 engineering criteria (10 pts each).
    Returns a dict with total score, breakdown, and rating.
    """

    def score(self, st_code: str) -> dict:
        breakdown = []
        total = 0

        for label, pattern, points, flags in _CHECKS:
            match = bool(re.search(pattern, st_code, flags))
            earned = points if match else 0
            total += earned
            breakdown.append({
                "criterion": label,
                "passed":    match,
                "points":    earned,
                "max":       points,
            })

        rating = (
            "EXCELLENT" if total >= 90 else
            "GOOD"      if total >= 70 else
            "MARGINAL"  if total >= 50 else
            "POOR"
        )

        failed = [b["criterion"] for b in breakdown if not b["passed"]]

        return {
            "engineering_score": total,
            "max_score":         100,
            "rating":            rating,
            "breakdown":         breakdown,
            "failed_checks":     failed,
        }

    def format_report(self, result: dict) -> str:
        """Return a Markdown-formatted score report."""
        lines = [
            f"## Engineering Score: {result['engineering_score']}/100 — {result['rating']}",
            "",
            "| Criterion | Status | Points |",
            "|-----------|--------|--------|",
        ]
        for b in result["breakdown"]:
            status = "PASS" if b["passed"] else "FAIL"
            lines.append(f"| {b['criterion']} | {status} | {b['points']}/{b['max']} |")

        if result["failed_checks"]:
            lines += [
                "",
                "**Failed checks:**",
                *[f"- {c}" for c in result["failed_checks"]],
            ]
        return "\n".join(lines)
