from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from backend.ld_module import generate_ld

router = APIRouter()

class LDRequest(BaseModel):
    domain: str

@router.post("/generate-ld")
def generate_ld_code(req: LDRequest, request: Request):
    email = request.headers.get("X-User-Email")
    if email:
        from backend.token_manager import check_and_update_tokens
        limit_check = check_and_update_tokens(email, 0)
        if limit_check.get("blocked"):
            raise HTTPException(status_code=403, detail="You have reached the 50k quota. Please continue with renewal.")

    rungs = generate_ld(req.domain)
    
    if email:
        from backend.token_manager import check_and_update_tokens
        used_tokens = (len(req.domain) // 4) + (len(str(rungs)) // 4) + 200
        check_and_update_tokens(email, used_tokens)
        
    return {
        "domain": req.domain,
        "rungs": [
            {
                "title": r.title,
                "ascii": r.ascii_rung,
                "notes": r.notes
            }
            for r in rungs
        ]
    }
