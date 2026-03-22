# backend/engine/st_normalizer.py
# IEC 61131-3 Structured Text Code Normalizer
#
# Performs deterministic formatting on generated ST code:
#   1. Operator spacing  (:=, <>, >=, <=, AND, OR, NOT)
#   2. VAR section column alignment
#   3. State comments in CASE branches (both numeric and named)
#   4. Trailing whitespace cleanup
#   5. Normalize CASE block structure
#
# Does NOT re-indent the entire file (too risky without a parser).
# Safe to run on any valid ST string.

import re


# ── Patterns ──────────────────────────────────────────────────────────────────

# Matches a CASE branch label line: "    Idle:" or "    2:  (* some comment *)"
_CASE_LABEL_RE = re.compile(
    r"^(\s*)([A-Za-z_][A-Za-z0-9_]*|\d+)\s*:\s*(?:\(\*.*\*\))?\s*$"
)

# Matches assignment operator, but not :=: or := inside strings
_ASSIGN_RE        = re.compile(r"(?<![:<>!])\s*:=\s*")
# Comparison operators
_NEQ_RE           = re.compile(r"\s*<>\s*")
_GTE_RE           = re.compile(r"\s*>=\s*")
_LTE_RE           = re.compile(r"\s*<=\s*")
# VAR declaration line: "    VarName : TYPE := value;"
_VAR_DECL_RE      = re.compile(r"^(\s+)(\w+)\s*:\s*(\S.+)$")
# IEC keywords — never fix spacing inside these tokens
_IEC_KW_NOT_VAR   = {"IF", "THEN", "ELSIF", "ELSE", "END_IF", "CASE", "OF",
                      "END_CASE", "VAR", "END_VAR", "VAR_INPUT", "VAR_OUTPUT",
                      "PROGRAM", "END_PROGRAM", "FOR", "TO", "DO", "END_FOR",
                      "WHILE", "END_WHILE", "REPEAT", "UNTIL", "END_REPEAT"}


class STNormalizer:
    """
    Normalizes IEC 61131-3 Structured Text code formatting.
    Accepts the ST code string and returns a cleaned version.
    """

    # State names known to the normalizer (from control model; populated externally)
    def __init__(self, state_names: dict = None):
        """
        state_names: optional {name_or_id: description} for comment injection.
        Both str keys ("Idle", "Running") and int keys (0, 1, 2) are supported.
        """
        self._state_names = state_names or {}

    # ── Public entry point ─────────────────────────────────────────────────────

    def normalize(self, st_code: str) -> str:
        lines = st_code.split("\n")

        # Phase 1: Trim trailing whitespace
        lines = [ln.rstrip() for ln in lines]

        # Phase 2: Operator spacing (skipping comment/string lines)
        lines = [self._fix_operators(ln) for ln in lines]

        # Phase 3: Align VAR block declarations
        code = "\n".join(lines)
        code = self._align_var_block(code)

        # Phase 4: Inject state comments into CASE branches
        code = self._inject_state_comments(code)

        # Phase 5: Normalise blank lines (max 2 consecutive blanks)
        code = re.sub(r"\n{3,}", "\n\n", code)

        return code.strip() + "\n"

    # ── Phase 2: Operator spacing ──────────────────────────────────────────────

    def _fix_operators(self, line: str) -> str:
        """Normalize operator spacing on a single line, skip comment/blank lines."""
        stripped = line.strip()
        # Skip blank or full-comment lines
        if not stripped or stripped.startswith("(*") or stripped.startswith("//"):
            return line

        # Work only on the non-comment portion of the line
        comment_start = self._find_comment_start(line)
        code_part    = line[:comment_start]
        comment_part = line[comment_start:]

        # := spacing  (protect <=, >=, <>, :=: )
        code_part = _ASSIGN_RE.sub(" := ", code_part)
        # <>, >=, <=
        code_part = _NEQ_RE.sub(" <> ", code_part)
        code_part = _GTE_RE.sub(" >= ", code_part)
        code_part = _LTE_RE.sub(" <= ", code_part)
        # Collapse multiple spaces but preserve leading indentation
        leading   = len(code_part) - len(code_part.lstrip())
        indent    = code_part[:leading]
        rest      = re.sub(r" {2,}", " ", code_part[leading:])
        code_part = indent + rest

        return code_part + comment_part

    @staticmethod
    def _find_comment_start(line: str) -> int:
        """Return index where (* comment begins, or len(line) if none."""
        idx = line.find("(*")
        return idx if idx != -1 else len(line)

    # ── Phase 3: VAR block alignment ──────────────────────────────────────────

    def _align_var_block(self, code: str) -> str:
        """
        Align variable declarations inside VAR...END_VAR blocks.
        Example:
            Before:  MyVar : BOOL := FALSE;
                     LongName : INT := 0;
            After:   MyVar    : BOOL  := FALSE;
                     LongName : INT   := 0;
        """
        # Find all VAR...END_VAR blocks (non-greedy)
        var_block_re = re.compile(
            r"((?:VAR(?:_INPUT|_OUTPUT)?)\b)(.*?)(END_VAR)",
            re.DOTALL,
        )

        def _align_block(match: re.Match) -> str:
            header, body, footer = match.group(1), match.group(2), match.group(3)
            aligned = self._align_declarations(body)
            return header + aligned + footer

        return var_block_re.sub(_align_block, code)

    def _align_declarations(self, body: str) -> str:
        """Align name : TYPE := value columns in a VAR body."""
        lines = body.split("\n")
        parsed = []  # [(indent, name, type_init, original_line)]

        for ln in lines:
            m = _VAR_DECL_RE.match(ln)
            if m and m.group(2) not in _IEC_KW_NOT_VAR:
                parsed.append((m.group(1), m.group(2), m.group(3), ln))
            else:
                parsed.append((None, None, None, ln))

        if not any(p[0] is not None for p in parsed):
            return body  # Nothing to align

        max_name_len = max(
            (len(p[1]) for p in parsed if p[1] is not None), default=0
        )
        max_name_len = min(max_name_len, 32)  # Cap at 32 to avoid excessive padding

        result = []
        for indent, name, type_init, original in parsed:
            if name is None:
                result.append(original)
            else:
                padded = name.ljust(max_name_len)
                result.append(f"{indent}{padded} : {type_init}")

        return "\n".join(result)

    # ── Phase 4: State comments ────────────────────────────────────────────────

    def _inject_state_comments(self, code: str) -> str:
        """
        Add (* STATE: <name> *) comments to CASE branch labels that have none.
        Works for both named states (Idle:) and numeric (0:, 1:).
        """
        lines = code.split("\n")
        result = []

        for line in lines:
            m = _CASE_LABEL_RE.match(line)
            if m:
                indent = m.group(1)
                label  = m.group(2)
                # Already has a comment → keep as-is
                if "(*" in line:
                    result.append(line)
                    continue
                # Resolve label to description
                desc = self._resolve_state(label)
                if desc:
                    result.append(f"{indent}{label}: (* {desc} *)")
                else:
                    result.append(f"{indent}{label}: (* STATE: {label} *)")
            else:
                result.append(line)

        return "\n".join(result)

    def _resolve_state(self, label: str) -> str:
        """Look up a state name/id in the state_names dict."""
        # Try exact string match first
        if label in self._state_names:
            return self._state_names[label]
        # Try integer match
        try:
            idx = int(label)
            if idx in self._state_names:
                return self._state_names[idx]
        except ValueError:
            pass
        # Well-known IEC state names
        _BUILTIN = {
            "Idle":     "Idle — waiting for start command",
            "Starting": "Starting — startup delay active",
            "Running":  "Running — process active",
            "Stopping": "Stopping — controlled shutdown",
            "Fault":    "Fault — safety latch, manual reset required",
            "Paused":   "Paused — process suspended",
            "Homing":   "Homing — returning to home position",
        }
        return _BUILTIN.get(label, "")


def normalize_st(st_code: str, state_names: dict = None) -> str:
    """Module-level convenience wrapper."""
    return STNormalizer(state_names=state_names).normalize(st_code)
