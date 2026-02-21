import re
from backend.brand_rules import BRAND_RULES


class IndustrialIECValidator:

    @staticmethod
    def validate_and_fix(code: str, brand: str = "siemens"):
        errors = []
        lines = code.splitlines()

        U = code.upper()

        if "PROGRAM" not in U or "END_PROGRAM" not in U:
            errors.append("Missing PROGRAM structure")

        if ".Q :=" in U:
            errors.append("Illegal timer output assignment")

        # Remove illegal timer writes
        fixed = []
        for l in lines:
            if ".Q :=" in l:
                continue
            fixed.append(l)

        return "\n".join(fixed), errors


def enforce_iec(code: str, brand: str = "siemens"):
    clean_code, errors = IndustrialIECValidator.validate_and_fix(code, brand)
    return clean_code, errors
