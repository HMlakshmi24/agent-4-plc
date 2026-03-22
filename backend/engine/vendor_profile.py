# backend/engine/vendor_profile.py

class VendorProfileInjector:
    """
    Layer 14: Adjusts pure IEC ST output to match vendor-specific style guides.
    """
    @staticmethod
    def apply(st_code: str, vendor: str, program_name: str) -> str:
        vendor = vendor.upper()
        
        if vendor == "SIEMENS":
            # Siemens SCL prefers REGION blocks for organization
            st_code = st_code.replace("(* ─── Edge Detection", "REGION Edge Detection\n    (*")
            st_code = st_code.replace("(* ─── Safety Overrides", "END_REGION\n\nREGION Safety Overrides\n    (*")
            st_code = st_code.replace("(* ─── State Machine", "END_REGION\n\nREGION State Machine\n    (*")
            st_code = st_code.replace("(* ─── Timer Calls", "END_REGION\n\nREGION Timers\n    (*")
            st_code = st_code.replace("(* ─── Deterministic Output", "END_REGION\n\nREGION Outputs\n    (*")
            st_code = st_code.replace("END_PROGRAM", "END_REGION\n\nEND_PROGRAM")
            
        elif vendor == "CODESYS":
            pass # Standard IEC is mostly 1:1 with Codesys
            
        elif vendor in ["ALLEN_BRADLEY", "ROCKWELL"]:
            # AB Studio 5000 ST has some minor capitalization differences
            pass
            
        return st_code
