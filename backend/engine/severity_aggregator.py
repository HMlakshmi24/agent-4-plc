# backend/engine/severity_aggregator.py
# Read-only severity aggregator — ONLY critical issues trigger a fix.
# Warnings are collected and returned to the user but never cause rewrites.

def aggregate_validation_results(results: dict) -> dict:
    """
    Aggregates validation results into a fix/approve decision.

    Only CRITICAL issues trigger a fix attempt.
    Warnings are informational only.
    """
    critical = results.get("critical", [])
    warning = results.get("warning", [])

    decision = "fix" if critical else "approve"

    return {
        "decision": decision,
        "critical": critical,
        "warning": warning
    }
