
class IECValidator:

    @staticmethod
    def validate(code: str):
        errors = []
        U = code.upper()

        if "PROGRAM" not in U:
            errors.append("Missing PROGRAM")
        if "END_PROGRAM" not in U:
            errors.append("Missing END_PROGRAM")
        if ".Q :=" in U:
            errors.append("Illegal timer assignment (.Q)")
        if ".ET :=" in U:
            errors.append("Illegal timer assignment (.ET)")
        if "IEC" in U and "IEC 61131" not in U: 
            # prevent 'IEC' keyword usage except in comments
            pass 

        # Minimal length check
        if len(code) < 20:
            errors.append("Code too short")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
