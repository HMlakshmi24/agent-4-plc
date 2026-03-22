# backend/engine/pid_validator.py
# P&ID Engineering Validation
#
# Validates a generated P&ID JSON layout for engineering completeness:
#   - Missing instrument loop numbers
#   - Missing pipe line IDs
#   - Equipment without connected instruments
#   - Missing control valves for control loops
#   - Missing transmitter tags
#   - Orphaned instruments (no connected equipment)
#
# Returns structured warnings — never modifies the P&ID data.

from __future__ import annotations
import re


# ── ISA instrument type categorisation ───────────────────────────────────────

# Types that are measurement transmitters (should have loop numbers)
_TRANSMITTER_TYPES = {"LT", "FT", "TT", "PT", "AT", "WT", "QT", "ST", "DT"}
# Types that are controllers
_CONTROLLER_TYPES  = {"LIC", "FIC", "TIC", "PIC", "AIC"}
# Types that are final control elements (valves)
_VALVE_TYPES       = {"XV", "HV", "FV", "TV", "PV", "CV", "BV", "LV", "EV"}
# Types that are switches/discrete
_SWITCH_TYPES      = {"LSH", "LSL", "FSH", "FSL", "TSH", "TSL", "PSH", "PSL",
                      "ZSH", "ZSL", "DE"}
# Equipment that should have at minimum one instrument
_INSTRUMENTED_EQUIPMENT = {"vertical_tank", "horizontal_tank", "vessel",
                            "centrifugal_pump", "heat_exchanger", "reactor",
                            "distillation_column", "compressor"}


class PIDValidator:
    """
    Validates a P&ID JSON layout for engineering completeness.
    Input:  pid_data dict (from the AI generator or fallback)
    Output: dict with warnings list and summary
    """

    def __init__(self, pid_data: dict):
        self.data       = pid_data or {}
        self.equipment  = self.data.get("equipment",     [])
        self.instruments = self.data.get("instruments",  [])
        self.pipes      = self.data.get("pipes",         [])
        self.loops      = self.data.get("control_loops", [])
        self.warnings:  list[str] = []

    def validate(self) -> dict:
        self._check_equipment_has_instruments()
        self._check_instruments_have_loop_numbers()
        self._check_pipe_line_ids()
        self._check_control_valves_for_loops()
        self._check_transmitter_tags()
        self._check_orphaned_instruments()
        self._check_minimum_instrumentation()

        return {
            "warnings":         self.warnings,
            "warning_count":    len(self.warnings),
            "equipment_count":  len(self.equipment),
            "instrument_count": len(self.instruments),
            "pipe_count":       len(self.pipes),
            "loop_count":       len(self.loops),
            "valid":            len(self.warnings) == 0,
        }

    # ── Checks ─────────────────────────────────────────────────────────────────

    def _check_equipment_has_instruments(self) -> None:
        """Every major piece of equipment should have at least one instrument."""
        eq_ids = {str(e.get("id", "")) for e in self.equipment}
        instrument_connections = {
            str(i.get("connected_to", "")) for i in self.instruments
        }

        for eq in self.equipment:
            eq_id   = str(eq.get("id", ""))
            eq_type = str(eq.get("type", "")).lower()
            if eq_type in _INSTRUMENTED_EQUIPMENT:
                if eq_id not in instrument_connections:
                    self.warnings.append(
                        f"Equipment '{eq_id}' ({eq_type}) has no connected instruments."
                    )

    def _check_instruments_have_loop_numbers(self) -> None:
        """Transmitters and controllers must have a loop number."""
        for inst in self.instruments:
            tag       = str(inst.get("tag", inst.get("id", "")))
            inst_type = str(inst.get("type", "")).upper()
            loop      = inst.get("loop", None)

            if inst_type in (_TRANSMITTER_TYPES | _CONTROLLER_TYPES):
                if not loop or str(loop).strip() == "":
                    self.warnings.append(
                        f"Instrument '{tag}' (type {inst_type}) is missing a loop number."
                    )

    def _check_pipe_line_ids(self) -> None:
        """Every pipe should have a line ID (id field, spec, or size)."""
        for pipe in self.pipes:
            pipe_id = str(pipe.get("id", "")).strip()
            spec    = str(pipe.get("spec", "")).strip()
            if not pipe_id or pipe_id.startswith("pipe_") or pipe_id.isdigit():
                if not spec:
                    from_eq = pipe.get("from", "?")
                    to_eq   = pipe.get("to",   "?")
                    self.warnings.append(
                        f"Pipe from '{from_eq}' to '{to_eq}' has no ISA line ID or spec."
                    )

    def _check_control_valves_for_loops(self) -> None:
        """Each control loop should have an associated control valve in the instruments list."""
        instrument_types = {
            str(i.get("type", "")).upper() for i in self.instruments
        }
        for loop in self.loops:
            loop_id  = loop.get("id", loop.get("tag", "?"))
            ctrl_dev = str(loop.get("controlled_device", "")).strip()
            # Check if controlled device is an actuator (valve/motor)
            # If it's a pump or motor, that's fine. But controllers should have a final element.
            has_valve = any(
                str(i.get("id", "")).startswith(ctrl_dev[:3])
                or ctrl_dev in str(i.get("id", ""))
                for i in self.instruments
            )
            # Check for control valve types in instrument list
            has_cv_type = bool(_VALVE_TYPES & instrument_types)
            if not has_valve and not has_cv_type:
                self.warnings.append(
                    f"Control loop '{loop_id}' has no associated control valve instrument tag."
                )

    def _check_transmitter_tags(self) -> None:
        """Instruments must have both 'id' and 'tag' fields correctly formatted."""
        isa_tag_pattern = re.compile(
            r"^[A-Z]{1,3}-\d{3,}$"  # e.g. LT-101, FIC-201
        )
        for inst in self.instruments:
            tag = str(inst.get("tag", "")).strip()
            if not tag:
                inst_id = inst.get("id", "?")
                self.warnings.append(
                    f"Instrument '{inst_id}' has no 'tag' field — ISA tag required."
                )
            elif not isa_tag_pattern.match(tag):
                # Allow some flexibility — warn but don't fail
                if not any(c.isdigit() for c in tag):
                    self.warnings.append(
                        f"Instrument tag '{tag}' does not follow ISA-5.1 format (e.g. LT-101)."
                    )

    def _check_orphaned_instruments(self) -> None:
        """Instruments should be connected to existing equipment IDs."""
        eq_ids = {str(e.get("id", "")) for e in self.equipment}
        for inst in self.instruments:
            connected = str(inst.get("connected_to", "")).strip()
            tag       = str(inst.get("tag", inst.get("id", "?")))
            if connected and connected not in eq_ids:
                self.warnings.append(
                    f"Instrument '{tag}' references '{connected}' which is not in the equipment list."
                )

    def _check_minimum_instrumentation(self) -> None:
        """Overall sanity check on minimum P&ID content."""
        if not self.equipment:
            self.warnings.append("P&ID contains no equipment — diagram may be empty or generation failed.")
        if not self.instruments:
            self.warnings.append("P&ID contains no instruments — ISA-5.1 requires at least one measurement loop.")
        if not self.pipes and len(self.equipment) > 1:
            self.warnings.append("P&ID has multiple equipment items but no pipe connections.")
        if not self.loops and len(self.equipment) > 2:
            self.warnings.append("P&ID has no control loops defined — consider adding at least one control loop.")
