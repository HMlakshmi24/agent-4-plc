
from backend.skeletons.st import get_st_skeleton
# LD and FBD skeletons removed

def get_skeleton(brand: str, language: str, domain: str) -> str:
    """
    Selects the correct IEC 61131-3 skeleton based on Brand, Language, and Domain.
    """
    lang = language.lower()

    if lang.upper() == "ST":
        return get_st_skeleton(domain)  # Using only domain as per definition
    # LD and FBD removed
    return get_st_skeleton(domain) # Default to ST
