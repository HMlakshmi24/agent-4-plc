"""
I/O Upload Route
POST /api/io/parse-csv   — parse CSV text → tag list JSON
POST /api/io/save-memory — save tag list to user's plant memory in MongoDB
GET  /api/io/memory      — load user's plant memory
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/io", tags=["io"])


class ParseCSVRequest(BaseModel):
    csv_text: str
    vendor: str = "SIEMENS"


class SaveMemoryRequest(BaseModel):
    plant_name: str
    vendor: str
    tags: List[dict]


@router.post("/parse-csv")
def parse_csv(req: ParseCSVRequest):
    """Parse a user's I/O list CSV into structured tag JSON."""
    from backend.engine.io_mapper import parse_io_csv, build_var_declarations
    try:
        tags = parse_io_csv(req.csv_text)
        if not tags:
            raise HTTPException(status_code=400, detail="No tags found. Check CSV format.")
        decls = build_var_declarations(tags, req.vendor)
        return {
            "tags":       tags,
            "var_input":  decls["var_input"],
            "var_output": decls["var_output"],
            "count":      len(tags),
            "inputs":     decls["inputs"],
            "outputs":    decls["outputs"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/save-memory")
async def save_memory(req: SaveMemoryRequest, request: Request):
    """Save parsed tag list as user's plant memory."""
    email = request.headers.get("X-User-Email")
    if not email:
        raise HTTPException(status_code=401, detail="Login required to save plant memory.")
    try:
        from backend.db import db
        await db.plant_memory.update_one(
            {"email": email, "plant_name": req.plant_name},
            {"$set": {
                "email":      email,
                "plant_name": req.plant_name,
                "vendor":     req.vendor,
                "tags":       req.tags,
            }},
            upsert=True
        )
        return {"saved": True, "plant_name": req.plant_name, "tag_count": len(req.tags)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory")
async def load_memory(request: Request, plant_name: Optional[str] = None):
    """Load user's saved plant memory (all plants or specific one)."""
    email = request.headers.get("X-User-Email")
    if not email:
        raise HTTPException(status_code=401, detail="Login required.")
    try:
        from backend.db import db
        query = {"email": email}
        if plant_name:
            query["plant_name"] = plant_name
        cursor = db.plant_memory.find(query, {"_id": 0})
        plants = await cursor.to_list(length=50)
        return {"plants": plants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{plant_name}")
async def delete_memory(plant_name: str, request: Request):
    """Delete a saved plant memory."""
    email = request.headers.get("X-User-Email")
    if not email:
        raise HTTPException(status_code=401, detail="Login required.")
    try:
        from backend.db import db
        await db.plant_memory.delete_one({"email": email, "plant_name": plant_name})
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
