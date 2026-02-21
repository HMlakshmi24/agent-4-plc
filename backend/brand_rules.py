
BRAND_RULES = {
    "siemens": {
        "allow_output_init": False,
        "require_output_reset": True,
        "strict_semicolons": True,
        "timer_must_scan": True
    },
    "codesys": {
        "allow_output_init": True,
        "require_output_reset": True,
        "strict_semicolons": True,
        "timer_must_scan": True
    },
    "allenbradley": {
        "allow_output_init": True,
        "require_output_reset": False,
        "strict_semicolons": False,
        "timer_must_scan": False
    },
    # Fallbacks that map roughly to above or generic
    "schneider": {
        "allow_output_init": True,
        "require_output_reset": True,
        "strict_semicolons": True,
        "timer_must_scan": True
    }
}
