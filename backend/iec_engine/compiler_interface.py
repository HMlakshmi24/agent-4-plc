import subprocess
import os
from typing import Tuple, List

# Fallback Internal Validators
from backend.iec_engine.fb_signature_validator import FBSignatureValidator
from backend.iec_engine.grammar_checker import IECGrammarChecker
from backend.engine.semantic_validator import SemanticValidator # Reuse V3.1 Semantic validator

class CompilerInterface:
    """
    Layer 4: The Authority.
    Attempts to compile using OpenPLC.
    Falls back to Internal 'Virtual Compiler' (Layer 3 chain) if OpenPLC is missing.
    """
    
    def __init__(self):
        # Check if OpenPLC compiler exists (Env Var or Default)
        env_cmd = os.getenv("OPENPLC_COMPILE_CMD")
        default_path = "./matiec/iec2c.exe"
        
        self.compiler_path = env_cmd if env_cmd else default_path
        
        # Check existence only if not a complex command (simple path check)
        # If user provides a full command string, we assume valid.
        self.has_compiler = bool(env_cmd) or os.path.exists(self.compiler_path)
        
        # Validators for fallback
        self.fb_validator = FBSignatureValidator()
        self.grammar = IECGrammarChecker()
        self.semantic = SemanticValidator()

    def compile(self, code: str, program_name: str) -> Tuple[bool, List[str]]:
        """
        Returns (Success, Errors)
        """
        
        # 1. Try Real Compiler (Future)
        if self.has_compiler:
            return self._compile_external(code)
            
        # 2. Virtual Compiler (Layer 3 + V3.1 Logic)
        return self._compile_virtual(code)
        
    def _compile_external(self, code: str) -> Tuple[bool, List[str]]:
        """
        Runs the actual OpenPLC compiler (iec2c).
        """
        try:
            # Create temp file
            with open("temp.st", "w") as f:
                f.write(code)
                
            cmd = [self.compiler_path, "temp.st"]
            # If Configured as a full string command, split it
            if " " in self.compiler_path and not os.path.exists(self.compiler_path):
                 cmd = self.compiler_path.split() + ["temp.st"]
                 
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, []
            else:
                # Parse stderr for errors
                return False, [result.stderr]
        except Exception as e:
            return False, [f"Compiler Execution Error: {str(e)}"]

    def _compile_virtual(self, code: str) -> Tuple[bool, List[str]]:
        """
        Simulates a compilation by running all our rigorous validators.
        """
        errors = []
        
        # A. Grammar
        errs = self.grammar.check_structure(code)
        errors.extend(errs)
        
        # B. FB Signatures
        errs = self.fb_validator.validate(code)
        errors.extend(errs)
        
        # C. Semantic (Undeclared Vars)
        missing_vars = self.semantic.validate(code)
        for v in missing_vars:
            errors.append(f"Undeclared identifier: '{v}'")
            
        return (len(errors) == 0), errors
