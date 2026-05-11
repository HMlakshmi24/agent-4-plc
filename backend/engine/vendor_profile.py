# backend/engine/vendor_profile.py

class VendorProfileInjector:
    """
    Layer 14: Vendor-specific post-processing.

    ARCH-3: REGION...END_REGION is NOT used on any platform.
    It is Siemens TIA Portal SCL only and breaks CoDeSys 3.5,
    Allen-Bradley Studio 5000, Schneider EcoStruxure, and Beckhoff TwinCAT.
    All section markers are (* ---- ... ---- *) comment style — works everywhere.
    """

    @staticmethod
    def apply(st_code: str, vendor: str, program_name: str) -> str:
        """
        Apply vendor-specific adjustments.
        Currently: no structural changes needed — generated code is already
        standard IEC 61131-3 compatible with all major platforms.
        """
        # No vendor-specific transformations — code is portable as-is.
        return st_code
