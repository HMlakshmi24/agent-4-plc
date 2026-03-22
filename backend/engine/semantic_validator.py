# backend/engine/semantic_validator.py
# READ-ONLY semantic industrial validator.
# Reports issues with severity — NEVER rewrites code.
# CRITICAL issues trigger a fix. WARNINGs are informational only.

import re


class SemanticValidator:
    """
    Industrial-grade semantic validator for IEC 61131-3 ST code.
    Read-only: detects and classifies issues, never modifies code.
    """

    def __init__(self, code: str):
        self.code = code
        self.code_upper = code.upper()
        self.critical = []
        self.warning = []

    def check_edge_detection_for_counters(self):
        """Counters that do `:= var + 1` must use R_TRIG."""
        increments = re.findall(r'(\w+)\s*:=\s*\1\s*\+\s*1', self.code)
        for var in increments:
            if 'R_TRIG' not in self.code_upper:
                self.critical.append(
                    f"Counter '{var}' increments without R_TRIG edge detection — possible scan-unsafe rapid fire."
                )

    def check_ton_timer_called(self):
        """TON declared in VAR block must also be called as a function block."""
        # Extract only the VAR block(s) to check for declarations
        var_blocks = re.findall(r'\bVAR\b.*?\bEND_VAR\b', self.code, re.DOTALL | re.IGNORECASE)
        ton_declared = any(
            re.search(r':\s*TON\b', block, re.IGNORECASE)
            for block in var_blocks
        )
        if ton_declared:
            # TON is declared — verify it is also called.
            # The template generates calls like: T_StartDelay(IN := ...)
            # NOT like: TON(IN := ...) — so we match the timer variable call pattern.
            timer_called = (
                # Pattern 1: variable name ending in timer-like name calling with IN :=
                re.search(r'\bT_\w+\s*\(\s*IN\s*:=', self.code, re.IGNORECASE)
                # Pattern 2: any TON literal call (old style)
                or re.search(r'\bTON\s*\(', self.code, re.IGNORECASE)
                # Pattern 3: any timer variable with (.Q access — means it was called
                or re.search(r'\bT_\w+\s*\.\s*Q\b', self.code, re.IGNORECASE)
            )
            if not timer_called:
                self.critical.append("TON timer is declared in VAR block but never called — timer will not run.")

    def check_outputs_assigned(self):
        """Outputs prefixed Q_ must have at least one assignment."""
        outputs = re.findall(r'\bQ_\w+\b', self.code)
        for output in set(outputs):
            if not re.search(rf'\b{re.escape(output)}\s*:=', self.code):
                self.critical.append(f"Output '{output}' is referenced but never assigned.")
            elif len(re.findall(rf'\b{re.escape(output)}\s*:=', self.code)) > 3:
                self.warning.append(
                    f"Output '{output}' is assigned in multiple places — prefer a single deterministic assignment at the bottom."
                )

    def check_clamp_protection(self):
        """Integer or counter variables should ideally have clamp/boundary checks."""
        if 'INT' in self.code_upper:
            has_clamp = '<' in self.code or '>' in self.code or 'MAX' in self.code_upper or 'MIN' in self.code_upper
            if not has_clamp:
                self.warning.append(
                    "No boundary clamp or comparison detected for integer values — consider adding max/min guards."
                )

    def check_timer_not_inside_if(self):
        """Warning: timers should be called unconditionally (outside IF blocks)."""
        # Heuristic: if TON( appears after IF and before END_IF, flag it
        if_blocks = re.findall(r'IF\b.*?END_IF;', self.code, re.DOTALL | re.IGNORECASE)
        for block in if_blocks:
            if re.search(r'\bTON\s*\(', block, re.IGNORECASE):
                self.warning.append("TON timer call detected inside an IF block — timers should be called unconditionally every scan for reliability.")
                break

    def check_program_wrapper(self):
        """PROGRAM ... END_PROGRAM must exist."""
        if 'PROGRAM' not in self.code_upper:
            self.critical.append("Missing 'PROGRAM' declaration — code is not a valid IEC 61131-3 program unit.")
        if 'END_PROGRAM' not in self.code_upper:
            self.critical.append("Missing 'END_PROGRAM' — program block is not properly closed.")

    def check_var_block(self):
        """VAR ... END_VAR must exist."""
        if 'VAR' not in self.code_upper:
            self.critical.append("Missing VAR block — all variables must be explicitly declared.")

    def check_fault_state_exists(self):
        """A FAULT state (or equivalent) must exist in a CASE block."""
        has_fault = bool(re.search(
            r'\bFault\s*:|STATE_FAULT\b|Q_Alarm\s*:=\s*TRUE|\(\*\s*FAULT\s*\*\)',
            self.code, re.IGNORECASE
        ))
        if not has_fault:
            self.warning.append(
                "No FAULT state or Q_Alarm := TRUE detected — industrial code must handle fault conditions explicitly."
            )

    def check_outputs_off_in_fault(self):
        """
        In a Fault or alarm state, Q_ outputs should be set to FALSE.
        Heuristic: find the Fault CASE branch and verify Q_xxx := FALSE.
        """
        fault_block_match = re.search(
            r'\bFault\s*:(.*?)(?:[A-Za-z_]+\s*:|ELSE\b|END_CASE\b)',
            self.code, re.DOTALL | re.IGNORECASE
        )
        if not fault_block_match:
            return  # No Fault branch found; check_fault_state_exists will warn

        block = fault_block_match.group(1)
        q_outputs = re.findall(r'\bQ_\w+\b', block)
        for out in set(q_outputs):
            # Check if this output is set to FALSE in the fault block
            if not re.search(rf'\b{re.escape(out)}\s*:=\s*FALSE\b', block, re.IGNORECASE):
                # Check if it's SET to TRUE (wrong in fault state)
                if re.search(rf'\b{re.escape(out)}\s*:=\s*TRUE\b', block, re.IGNORECASE):
                    self.warning.append(
                        f"Output '{out}' is set TRUE in Fault state — actuators should be OFF during fault."
                    )

    def check_running_state_has_stop_condition(self):
        """
        The Running state (or equivalent active state) must have at least
        one condition that transitions away (stop or fault transition).
        """
        running_match = re.search(
            r'\b(?:Running|Run|Active|Operating)\s*:(.*?)(?:[A-Za-z_]+\s*:|ELSE\b|END_CASE\b)',
            self.code, re.DOTALL | re.IGNORECASE
        )
        if not running_match:
            return  # Running state not found by name — skip check

        block = running_match.group(1)
        # Look for a State/M_State assignment (any transition out)
        has_transition = bool(re.search(
            r'(?:M_State|State)\s*:=\s*\w+', block, re.IGNORECASE
        ))
        if not has_transition:
            self.warning.append(
                "Running state has no exit transition — there must be a stop or fault condition in the Running state."
            )

    def check_declared_timers_are_used(self):
        """Every T_ timer declared in VAR must also be called in the program body."""
        var_blocks = re.findall(
            r'\bVAR\b.*?\bEND_VAR\b', self.code, re.DOTALL | re.IGNORECASE
        )
        declared_timers = []
        for block in var_blocks:
            # Match: T_SomeName : TON or : TOF
            timers = re.findall(
                r'\b(T_\w+)\s*:\s*(?:TON|TOF|TP)\b', block, re.IGNORECASE
            )
            declared_timers.extend(timers)

        program_body_match = re.search(
            r'\bEND_VAR\b(.*)', self.code, re.DOTALL | re.IGNORECASE
        )
        if not program_body_match:
            return
        body = program_body_match.group(1)

        for timer in declared_timers:
            # Timer must be called as a function block: T_Name(IN := ...)
            if not re.search(
                rf'\b{re.escape(timer)}\s*\(',  body, re.IGNORECASE
            ):
                self.warning.append(
                    f"Timer '{timer}' is declared but never called — it will not run."
                )

    def check_alarm_output_with_fault(self):
        """If a Fault state or E-Stop exists, an alarm output (Q_Alarm) should also exist."""
        has_fault_logic = bool(re.search(
            r'\bFault\s*:|I_EStop\b', self.code, re.IGNORECASE
        ))
        has_alarm_output = bool(re.search(
            r'\bQ_Alarm\b|\bQ_\w*Alarm\w*\b|\bQ_\w*Fault\w*\b',
            self.code, re.IGNORECASE
        ))
        if has_fault_logic and not has_alarm_output:
            self.warning.append(
                "Fault/E-Stop logic is present but no Q_Alarm output is declared — consider adding a diagnostic alarm output."
            )

    def check_startbutton_edge_detection(self):
        """I_Start / I_Stop used directly in IF conditions should have R_TRIG protection.

        Direct use of a latched boolean as the sole start condition can cause
        re-triggering across scans.  We flag it as a WARNING only (some designs
        intentionally use level-sensitive start).
        """
        # If R_TRIG (or F_TRIG) is present anywhere, the designer is aware of
        # edge detection — skip the check entirely.
        if re.search(r'\b[RF]_TRIG\b', self.code, re.IGNORECASE):
            return

        # Look for I_Start or I_Stop used directly as a condition without edge FB
        direct_start = re.search(
            r'\bIF\b[^;]*\bI_Start\b[^;]*\bTHEN\b', self.code, re.IGNORECASE | re.DOTALL
        )
        direct_stop  = re.search(
            r'\bIF\b[^;]*\bI_Stop\b[^;]*\bTHEN\b',  self.code, re.IGNORECASE | re.DOTALL
        )
        if direct_start or direct_stop:
            self.warning.append(
                "I_Start / I_Stop used directly in IF conditions without R_TRIG edge detection — "
                "consider using R_TRIG to prevent re-triggering across scan cycles."
            )

    def validate(self) -> dict:
        """Run all checks and return structured result."""
        # Original checks
        self.check_program_wrapper()
        self.check_var_block()
        self.check_edge_detection_for_counters()
        self.check_ton_timer_called()
        self.check_outputs_assigned()
        self.check_timer_not_inside_if()
        self.check_clamp_protection()
        # Extended engineering checks
        self.check_fault_state_exists()
        self.check_outputs_off_in_fault()
        self.check_running_state_has_stop_condition()
        self.check_declared_timers_are_used()
        self.check_alarm_output_with_fault()
        self.check_startbutton_edge_detection()

        return {
            "critical": self.critical,
            "warning":  self.warning,
        }
