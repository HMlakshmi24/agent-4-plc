
import sys
import os
# Add current dir to path so backend module is found
sys.path.append(os.getcwd())

from backend.industrial_iec_validator import IndustrialIECValidator

def compile_check(code: str):
    result = IndustrialIECValidator.validate(code)
    return result["valid"], result["errors"]

if __name__ == "__main__":
    # In Docker or Pipeline, read from stdin
    # For now, simplistic input reading
    import sys
    code = sys.stdin.read()
    ok, errors = compile_check(code)
    if ok:
        print("COMPILE_OK")
    else:
        print("COMPILE_FAIL")
        for e in errors:
            print(e)
