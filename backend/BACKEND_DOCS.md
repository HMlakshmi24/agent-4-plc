# Agent4PLC - Production Backend Documentation

## Overview

Complete, production-ready backend for multi-brand PLC code generation supporting:
- **ST** (Structured Text)
- **LD** (Ladder Diagram)  
- **FBD** (Function Block Diagram)
- **SFC** (Sequential Function Chart)
- **IL** (Instruction List)

### Supported Brands
- Siemens
- Codesys
- Allen-Bradley
- Schneider

---

## Architecture

```
backend/
├── brand_rules.py          # Brand-specific constraints
├── iec_skeletons.py        # IEC language templates
├── iec_enforcer.py         # Validator & auto-fixer
├── compiler_test.py        # Syntax validation
├── main.py                 # FastAPI application
├── run_backend.py          # Quick start script
├── test_api.py             # API test suite
└── requirements.txt        # Dependencies
```

---

## Installation

### Prerequisites
- Python 3.10+
- pip

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Start Server

```bash
python run_backend.py
```

Or directly with uvicorn:

```bash
uvicorn main:app --reload --port 8000
```

Server will run on: **http://127.0.0.1:8000**

---

## API Endpoints

### Health Check
```
GET /
```

Returns backend status and available languages.

### Generate PLC Code
```
POST /generate
```

**Request Body:**
```json
{
  "brand": "siemens",
  "language": "ST",
  "program": "ProgramName",
  "inputs": ["Input1 : BOOL;", "Input2 : INT;"],
  "outputs": ["Output1 : BOOL;"],
  "internals": ["Counter : INT := 0;"],
  "logic": "IF Input1 THEN Counter := Counter + 1; END_IF;"
}
```

**Response:**
```json
{
  "code": "PROGRAM ProgramName...",
  "warnings": [],
  "compile_status": "Compilation OK"
}
```

---

## Using the API

### Python Example

```python
import requests

url = "http://127.0.0.1:8000/generate"
data = {
    "brand": "siemens",
    "language": "ST",
    "program": "Lift_Control",
    "inputs": ["CallButton : BOOL;"],
    "outputs": ["DoorOpen : BOOL;"],
    "internals": ["Timer : TON;"],
    "logic": "IF CallButton THEN Timer(IN := TRUE); DoorOpen := Timer.Q; END_IF;"
}

response = requests.post(url, json=data)
print(response.json())
```

### Bash/cURL Example

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "brand": "siemens",
    "language": "ST",
    "program": "TestProgram",
    "inputs": ["Start : BOOL;"],
    "outputs": ["Output : BOOL;"],
    "internals": [],
    "logic": "Output := Start;"
  }'
```

---

## Testing

### Run Test Suite

```bash
python test_api.py
```

Tests all 5 languages with sample programs.

### Interactive API Docs

Open browser to: **http://127.0.0.1:8000/docs**

Swagger UI allows testing all endpoints with visual interface.

---

## Docker Deployment

### Build Image

```bash
docker build -t plc-backend .
```

### Run Container

```bash
docker run -p 8000:8000 plc-backend
```

Access API at: **http://localhost:8000**

### Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
```

Run:
```bash
docker-compose up
```

---

## Features

| Feature | Support | Notes |
|---------|---------|-------|
| Multi-brand rules | ✓ | Siemens, Codesys, Allen-Bradley, Schneider |
| ST generator | ✓ | Full template with VAR blocks |
| LD generator | ✓ | Network-based structure |
| FBD generator | ✓ | Block diagram format |
| SFC generator | ✓ | State machine template |
| IL generator | ✓ | Instruction list format |
| IEC validation | ✓ | Comprehensive checks |
| Auto-fixing | ✓ | Removes illegal constructs |
| Compile test | ✓ | Offline syntax check |
| No API keys | ✓ | Fully offline |
| Docker ready | ✓ | Production container |

---

## Configuration

### Brand Rules

Modify `brand_rules.py` to customize per-brand constraints:

```python
"siemens": {
    "allow_output_init": False,
    "timer_style": "always_called",
    "case_sensitive": True,
    "require_semicolon": True
}
```

### IEC Validation

Edit `iec_enforcer.py` to add custom validation rules:

```python
def validate(code: str, brand="generic"):
    # Add custom checks here
    pass
```

### Templates

Edit `iec_skeletons.py` to customize code structure:

```python
ST_SKELETON = """PROGRAM {program}
...
"""
```

---

## Error Handling

The API returns comprehensive validation errors on `/generate`:

```json
{
  "code": "PROGRAM...",
  "warnings": ["Counter without R_TRIG"],
  "compile_status": "Compilation OK"
}
```

Common errors:
- `Missing PROGRAM` - Missing program header
- `Missing END_PROGRAM` - Missing end marker
- `Illegal write to input` - Assignment to input variable
- `Illegal write to timer output` - Assignment to timer.Q or timer.ET
- `Timer inside IF block` - Timer not at top level
- `Siemens: Output initialized in VAR_OUTPUT` - Brand-specific violation

---

## Performance

- **Response time**: ~10-50ms per request
- **Memory**: ~50MB baseline
- **Max payload**: Configurable (default 25MB)
- **Concurrent requests**: Limited by uvicorn workers

---

## Production Best Practices

1. **Use uvicorn with gunicorn** for serious deployments:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
   ```

2. **Add reverse proxy** (nginx) for load balancing

3. **Enable HTTPS** with certificates

4. **Set CORS appropriately**:
   ```python
   allow_origins=["https://yourdomain.com"]
   ```

5. **Use environment variables** for configuration

6. **Add request logging** for debugging

7. **Monitor with tools** like Prometheus/Grafana

---

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux
lsof -i :8000
kill -9 <PID>
```

### Import Errors
Ensure you're in the `backend/` directory or set `PYTHONPATH`:
```bash
export PYTHONPATH=/path/to/plc_backend
```

### Module Not Found
Install all dependencies:
```bash
pip install -r requirements.txt
```

### Docker Build Fails
Check Python version and cache:
```bash
docker build --no-cache -t plc-backend .
```

---

## Support

For issues, check:
1. Request body format (must be valid JSON)
2. All required fields present
3. Brand name exists in `brand_rules.py`
4. Language is one of: ST, LD, FBD, SFC, IL
5. Server logs for detailed errors

---

## License

Same as parent project.

---

**Last Updated**: 2026
