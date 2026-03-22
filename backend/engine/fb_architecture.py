# backend/engine/fb_architecture.py

class FBArchitectureInjector:
    """
    Layer 15: Upgrades from a generic PROGRAM template to a modular 
    FUNCTION_BLOCK definition preferred in enterprise PLC projects.
    """
    @staticmethod
    def apply(st_code: str, program_name: str) -> str:
        # Replace PROGRAM with FUNCTION_BLOCK
        st_code = st_code.replace(f"PROGRAM {program_name}", f"FUNCTION_BLOCK FB_{program_name}")
        st_code = st_code.replace("END_PROGRAM", "END_FUNCTION_BLOCK")
        
        # Split VAR into VAR_INPUT, VAR_OUTPUT, VAR based on comments if available
        # Note: In the locked template, we rely on comments (* Inputs *) etc.
        st_code = st_code.replace("VAR\n    (* Inputs *)", "VAR_INPUT")
        st_code = st_code.replace("    (* Outputs *)", "END_VAR\nVAR_OUTPUT")
        st_code = st_code.replace("    (* Analog Values *)", "END_VAR\nVAR")
        st_code = st_code.replace("    (* Internal States *)", "END_VAR\nVAR")
        # Ensure we don't duplicate END_VAR blocks if sections are missing
        # A more robust regex replacement could go here, but this is the concept.
        
        return st_code
