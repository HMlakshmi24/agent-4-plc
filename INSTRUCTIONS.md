# Agent4PLC — Complete Setup & Operations Guide

> **Status:** Backend ✅ on `http://localhost:8001` · Frontend ✅ on `http://localhost:5174`

---

## 🐍 Python & Virtual Environment

This project requires **Python 3.10** (NOT the system default Python 3.14 — it lacks pre-built wheels for `openai`, `cffi` etc.).

### Check what Python versions are installed
```powershell
py -0p
```
You should see both `-V:3.14` and `-V:3.10` listed.

### Create the venv (one-time, already done)
```powershell
cd "c:\Users\hmlak\OneDrive\Desktop\office works\agent4plc\agent-4-plc"
py -3.10 -m venv venv310
```
The `venv310/` folder lives at the **project root** alongside `backend/` and `frontend/`.

---

## 🔑 Where to Put API Keys & MongoDB

### File: Root `.env`
📄 [.env](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/.env)

| Line | Key | What to put |
|------|-----|------------|
| **3** | `MONGO_URI=` | Your full MongoDB Atlas connection string |
| **12** | `OPENAI_API_KEY=` | Your OpenAI or OpenRouter API key |
| **13** | `OPENAI_BASE_URL=` | `https://api.openai.com/v1` (OpenAI) or `https://openrouter.ai/api/v1` (OpenRouter) |
| **4** | `GEMINI_API_KEY=` | Google Gemini API key (optional) |

**Example `.env`:**
```env
MONGO_URI="mongodb+srv://USERNAME:PASSWORD@cluster.mongodb.net/?retryWrites=true&w=majority&appName=agent4plc"
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
OPENAI_BASE_URL=https://api.openai.com/v1
GEMINI_API_KEY=AIzaSy...
JWT_SECRET="your-secret-key"
PLC_OUTPUT_DIR=backend/plc
```

### Where keys are READ in code

| Key | File | Line |
|-----|------|------|
| `MONGO_URI` | [backend/db.py](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/backend/db.py#L10) | **Line 10** |
| `OPENAI_API_KEY` | [backend/openai_client.py](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/backend/openai_client.py#L7) | **Line 7** |
| `OPENAI_BASE_URL` | [backend/openai_client.py](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/backend/openai_client.py#L8) | **Line 8** |
| `JWT_SECRET` | [backend/utils.py](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/backend/utils.py#L22) | **Line 22** |
| `GEMINI_API_KEY` | [backend/routes/langchain_create_agent.py](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/backend/routes/langchain_create_agent.py) | Used by Google Gemini chain |

---

## 🚀 Running the Project

### Backend
```powershell
# From project root — ALWAYS use venv310
cd "c:\Users\hmlak\OneDrive\Desktop\office works\agent4plc\agent-4-plc"
$env:PYTHONUTF8="1"
.\venv310\Scripts\python backend\main.py
```
✅ Server starts at **http://localhost:8001**
📄 Entry point: [backend/main.py](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/backend/main.py) — Line 67 sets `port=8001`

> **Or just double-click:** [start_backend.bat](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/start_backend.bat) — auto-kills the port and sets UTF-8.

### Frontend
```powershell
cd "c:\Users\hmlak\OneDrive\Desktop\office works\agent4plc\agent-4-plc\frontend"
npm install        # first time only
npm run dev
```
✅ Dev server starts at **http://localhost:5173** (or 5174 if 5173 is busy)

---

## 📋 All Changes Made (This Session)

### 1. `requirements.txt` — Fixed broken versions
📄 [requirements.txt](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/requirements.txt)

Replaced non-existent version pins with Python 3.10 compatible flexible ranges:
- `cffi==2.0.0` → **removed** (no wheel for Python 3.10/3.14)  
- `openai==2.16.0` → `openai>=1.30.0,<1.57.0` (1.57+ requires Python 3.11+)  
- `langchain==1.2.7` → `langchain>=0.2.0,<0.3.0` (0.2.x series for Python 3.10)  
- `annotated-doc==0.0.4` → **removed** (fake package)

### 2. `backend/db.py` — Fixed `.env` loading path
📄 [backend/db.py](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/backend/db.py) — **Lines 1-9**

```python
# Before (broken):
load_dotenv()  # only searched current directory → missed MONGO_URI

# After (fixed):
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)  # always loads root .env
```

### 3. `backend/main.py` — Port fix + UTF-8 fix
📄 [backend/main.py](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/backend/main.py)

- **Lines 2-8:** Added UTF-8 stdout/stderr wrapper (fixes `UnicodeEncodeError` with emoji in terminal)
- **Line 68:** Changed `port=8000` → `port=8001`
- **Lines 68-71:** Switched from `uvicorn.run()` to `uvicorn.Server(Config(...))` for cleaner restarts

### 4. `frontend/package.json` — Removed incompatible package
📄 [frontend/package.json](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/frontend/package.json) — **Line 16 (removed)**

- Removed `"mongodb": "^6.20.0"` — this is a server-only Node.js driver that breaks Vite bundling in the browser

### 5. `.env` — Added missing variable
📄 [.env](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/.env) — **Line 2**

- Added `PLC_OUTPUT_DIR=backend/plc`

### 6. `.gitignore` — Excluded generated files (cleared 10k pending changes)
📄 [.gitignore](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/.gitignore)

Added: `venv310/`, `*.db`, `*.log`, `dist/`, `pip_output.txt`, `__pycache__/`

### 7. `frontend/src/config/api.js` — Fixed API port
📄 [frontend/src/config/api.js](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/frontend/src/config/api.js) — **Line 4**

```js
// Before: export const API = "http://localhost:8000";
// After:
export const API = import.meta.env.VITE_API_URL || "http://localhost:8001";
```

### 8. `frontend/src/components/LoginModal.jsx` — Fixed 4 hardcoded ports + added import
📄 [frontend/src/components/LoginModal.jsx](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/frontend/src/components/LoginModal.jsx)

- **Line 5:** Added `import { API } from "../config/api";`
- **Lines 47, 119, 140, 358:** Replaced `"http://localhost:8000"` with `API`

### 9. `frontend/src/components/InfoModals.jsx` — Fixed hardcoded port
📄 [frontend/src/components/InfoModals.jsx](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/frontend/src/components/InfoModals.jsx) — **Line 6**

- Changed fallback from `8000` → `8001`

### 10. `start_backend.bat` — New helper script
📄 [start_backend.bat](file:///c:/Users/hmlak/OneDrive/Desktop/office%20works/agent4plc/agent-4-plc/start_backend.bat)

- Kills any existing process on port 8001 before starting
- Sets `PYTHONUTF8=1` to prevent emoji crash
- Activates `venv310` and starts the backend

---

## 🌐 Deploying to Production

### Backend → Render
1. Push to GitHub
2. Create **Web Service** on [render.com](https://render.com)
3. Settings:
   - **Root Directory:** leave blank (use project root)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables** on Render:
   - `MONGO_URI` = your Atlas URI
   - `OPENAI_API_KEY` = your key
   - `OPENAI_BASE_URL` = `https://api.openai.com/v1`
   - `JWT_SECRET` = a strong random string
   - `PYTHONUTF8` = `1`

### Frontend → Vercel
1. Import repo on [vercel.com](https://vercel.com)
2. **Root Directory:** `frontend`
3. **Environment Variables** on Vercel:
   - `VITE_API_URL` = `https://your-render-backend.onrender.com`
4. Deploy

---

## 🔧 API Endpoints Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | None | Create account |
| POST | `/auth/login` | None | Get JWT token |
| POST | `/auth/forgot-password` | None | Send OTP |
| POST | `/auth/reset-password` | None | Reset password |
| GET | `/profile/me` | ✅ JWT | Get user profile |
| PUT | `/profile/update` | ✅ JWT | Update settings |
| POST | `/generate` | Optional | Generate ST/LD PLC code |
| GET | `/history/` | ✅ JWT | Get generation history |
| GET | `/api/tokens/` | Optional | Check token usage |
| POST | `/api/ai-help/` | Optional | AI chatbot |
| POST | `/api/support/ticket` | ✅ JWT | Submit support ticket |
| POST | `/api/hmi/generate` | Optional | Generate HMI layout |

> Swagger docs available at: **http://localhost:8001/docs**