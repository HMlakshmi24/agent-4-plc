"""
Perfect PLC API Route - Ultimate IEC 61131-3 Generation Endpoint
Integrates the Perfect PLC Pipeline with FastAPI
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import logging
from datetime import datetime

from backend.perfect_plc_pipeline import generate_perfect_iec_plc_code

# Setup router
router = APIRouter(prefix="/perfect-plc", tags=["Perfect PLC"])

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PerfectPLCRequest(BaseModel):
    """Request model for Perfect PLC generation"""
    requirement: str
    brand: str = "SIEMENS"  # SIEMENS, CODESYS, ALLEN_BRADLEY, SCHNEIDER, GENERIC
    api_key: Optional[str] = None
    strict_mode: bool = True
    language: str = "ST"  # Currently only ST is supported

class PerfectPLCResponse(BaseModel):
    """Response model for Perfect PLC generation"""
    success: bool
    iec_compliant: bool
    compliance_score: int
    final_code: str
    requirement: str
    brand: str
    attempts_required: int
    errors: List[str] = []
    warnings: List[str] = []
    generation_details: Dict = {}
    timestamp: str

# ============================================================================
# MAIN GENERATION ENDPOINT
# ============================================================================

@router.post("/generate", response_model=PerfectPLCResponse)
async def generate_perfect_plc(request: PerfectPLCRequest):
    """
    Generate Perfect IEC 61131-3 Compliant PLC Code
    
    This endpoint uses the Perfect PLC Pipeline which includes:
    - Multi-pass requirement analysis
    - Template-locked IEC structure generation
    - Comprehensive validation with zero tolerance
    - Automated error fixing
    - Multiple generation attempts
    
    The generated code is guaranteed to be IEC 61131-3 compliant or the best
    possible effort with detailed compliance reporting.
    """
    
    try:
        logger.info(f"Perfect PLC Generation Request:")
        logger.info(f"  Brand: {request.brand}")
        logger.info(f"  Requirement: {request.requirement[:100]}...")
        logger.info(f"  Strict Mode: {request.strict_mode}")
        
        # Validate brand
        supported_brands = ["SIEMENS", "CODESYS", "ALLEN_BRADLEY", "SCHNEIDER", "GENERIC"]
        if request.brand.upper() not in supported_brands:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported brand: {request.brand}. Supported: {supported_brands}"
            )
        
        # Validate requirement length
        if len(request.requirement.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Requirement too short. Please provide detailed description."
            )
        
        # Generate perfect PLC code
        start_time = datetime.now()
        
        result = generate_perfect_iec_plc_code(
            requirement=request.requirement,
            brand=request.brand,
            api_key=request.api_key,
            strict_mode=request.strict_mode
        )

        # Ensure result is a dict (safety guard)
        if not isinstance(result, dict):
            result = {"requirement": request.requirement, "brand": request.brand,
                      "final_code": str(result), "iec_compliant": False,
                      "compliance_score": 0, "attempts": [], "success": False,
                      "errors": ["Pipeline returned non-dict result"], "warnings": [],
                      "generation_details": {}}
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Generation completed in {processing_time:.2f}s")
        logger.info(f"  IEC Compliant: {result['iec_compliant']}")
        logger.info(f"  Compliance Score: {result['compliance_score']}")
        logger.info(f"  Attempts: {len(result['attempts'])}")
        
        # Prepare response
        response = PerfectPLCResponse(
            success=result["success"],
            iec_compliant=result["iec_compliant"],
            compliance_score=result["compliance_score"],
            final_code=result["final_code"],
            requirement=result["requirement"],
            brand=result["brand"],
            attempts_required=len(result["attempts"]),
            errors=[e["message"] if isinstance(e, dict) else str(e) for e in result.get("errors", [])],
            warnings=[w["message"] if isinstance(w, dict) else str(w) for w in result.get("warnings", [])],
            generation_details=result.get("generation_details", {}),
            timestamp=end_time.isoformat()
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Perfect PLC generation failed: {str(e)}\n{tb}")
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)} | trace: {tb.splitlines()[-3]}"
        )

# ============================================================================
# VALIDATION ENDPOINT
# ============================================================================

class ValidationRequest(BaseModel):
    """Request model for code validation"""
    code: str
    strict_mode: bool = True

class ValidationResponse(BaseModel):
    """Response model for code validation"""
    is_valid: bool
    iec_compliant: bool
    compliance_score: int
    critical_errors: List[Dict] = []
    errors: List[Dict] = []
    warnings: List[Dict] = []
    validation_details: Dict = {}
    timestamp: str

@router.post("/validate", response_model=ValidationResponse)
async def validate_iec_code(request: ValidationRequest):
    """
    Validate IEC 61131-3 Structured Text Code
    
    Performs comprehensive validation including:
    - Structure validation (PROGRAM, VAR sections)
    - Syntax validation (parentheses, terminators)
    - Safety validation (edge detection, bounded counters)
    - IEC standard compliance
    - Best practice checking
    """
    
    try:
        from backend.ultimate_iec_validator import UltimateIECValidator
        
        validator = UltimateIECValidator(request.strict_mode)
        validation_result = validator.validate_code(request.code)
        
        response = ValidationResponse(
            is_valid=validation_result["is_valid"],
            iec_compliant=validation_result["iec_compliant"],
            compliance_score=validation_result["compliance_score"],
            critical_errors=validation_result.get("critical_errors", []),
            errors=validation_result.get("errors", []),
            warnings=validation_result.get("warnings", []),
            validation_details=validation_result.get("validation_details", {}),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Validation completed - Score: {validation_result['compliance_score']}/100")
        
        return response
        
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )

# ============================================================================
# COMPLIANCE REPORT ENDPOINT
# ============================================================================

class ReportRequest(BaseModel):
    """Request model for compliance report"""
    generation_result: Dict

@router.post("/report")
async def generate_compliance_report(request: ReportRequest):
    """
    Generate Detailed Compliance Report
    
    Creates a comprehensive report showing:
    - Overall compliance status
    - Detailed error analysis
    - Recommendations for improvement
    - Generation attempt summary
    """
    
    try:
        from backend.perfect_plc_pipeline import PerfectPLCPipeline
        
        pipeline = PerfectPLCPipeline()
        report = pipeline.generate_compliance_report(request.generation_result)
        
        return {
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )

# ============================================================================
# SUPPORTED BRANDS ENDPOINT
# ============================================================================

@router.get("/brands")
async def get_supported_brands():
    """Get list of supported PLC brands"""
    return {
        "supported_brands": [
            {
                "name": "SIEMENS",
                "description": "Siemens TIA Portal / STEP 7",
                "prefixes": {"input": "I_", "output": "Q_", "internal": "M_"}
            },
            {
                "name": "CODESYS", 
                "description": "CODESYS Development System",
                "prefixes": {"input": "", "output": "", "internal": ""}
            },
            {
                "name": "ALLEN_BRADLEY",
                "description": "Rockwell Automation Studio 5000",
                "prefixes": {"input": "", "output": "", "internal": ""}
            },
            {
                "name": "SCHNEIDER",
                "description": "Schneider Electric EcoStruxure",
                "prefixes": {"input": "%I", "output": "%Q", "internal": "%M"}
            },
            {
                "name": "GENERIC",
                "description": "Generic IEC 61131-3",
                "prefixes": {"input": "I_", "output": "Q_", "internal": "M_"}
            }
        ],
        "default": "SIEMENS"
    }

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Perfect PLC API",
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "capabilities": [
            "IEC 61131-3 ST generation",
            "Multi-brand support", 
            "Zero-tolerance validation",
            "Automated error fixing",
            "Compliance reporting"
        ]
    }

# ============================================================================
# EXAMPLE USAGE ENDPOINT
# ============================================================================

@router.get("/example")
async def get_example_request():
    """Get example request for testing"""
    return {
        "example_request": {
            "requirement": "Design a parking gate control system with entry/exit sensors, capacity limit of 100 cars, emergency stop button, and automatic gate open/close control with safety interlocks.",
            "brand": "SIEMENS",
            "strict_mode": True,
            "language": "ST"
        },
        "expected_features": [
            "PROGRAM/END_PROGRAM structure",
            "VAR_INPUT/VAR_OUTPUT/VAR sections", 
            "R_TRIG edge detection for sensors",
            "Bounded counter for car count",
            "State machine with CASE statement",
            "Timer calls outside IF blocks",
            "Output initialization to FALSE",
            "Safety interlocks"
        ]
    }
