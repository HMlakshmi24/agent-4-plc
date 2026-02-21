"""Top-level wrapper to expose backend.ultra_strict_validator as a module

This file allows tests and scripts to import `ultra_strict_validator` directly.
"""
from backend.ultra_strict_validator import UltraStrictIECValidator, comprehensive_iec_audit

__all__ = ["UltraStrictIECValidator", "comprehensive_iec_audit"]
