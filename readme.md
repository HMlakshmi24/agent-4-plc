# Agent4PLC - Setup & Deployment Guide

## Local Setup (Running Offline)

Steps to run the system locally on a new PC.

### Backend Commands (Windows / PowerShell)
1. Open a terminal in the project root.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv310
   venv310\Scripts\activate
   ```
3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create environment file:
   ```bash
   notepad backend\.env
   ```
   Example contents:
   ```env
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/?retryWrites=true&w=majority
   OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY
   ```
5. Run the backend API:
   ```bash
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
6. Open API docs:
   ```
   http://127.0.0.1:8000/docs
   ```

### Backend Commands (macOS/Linux)
1. Open a terminal in the project root.
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv310
   source venv310/bin/activate
   ```
3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create environment file:
   ```bash
   cat > backend/.env << 'EOF'
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/?retryWrites=true&w=majority
   OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY
   EOF
   ```
5. Run the backend API:
   ```bash
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
6. Open API docs:
   ```
   http://127.0.0.1:8000/docs
   ```

### Frontend Commands (Windows / PowerShell)
1. Open a new terminal in the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open the app:
   ```
   http://localhost:5173
   ```

### Frontend Commands (macOS/Linux)
1. Open a new terminal in the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open the app:
   ```
   http://localhost:5173
   ```

### Optional Dev Commands
Run backend without auto-reload:
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

If you see port conflicts:
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Deployment Guide (Render & Vercel)

This section details how to deploy your frontend to **Vercel** and your backend to **Render**.

### Where are keys used in the code?

If you need to manually check where the configurations are used or hardcode them directly, here are the exact files and lines:

**A. MongoDB Connection:**
- **File:** `backend/db.py`
- **Line 8:** `MONGO_URI = os.getenv("MONGO_URI")`
- *(To hardcode instead: `MONGO_URI = "mongodb+srv://..."`)*

**B. OpenAI API Key:**
There are four places where the OpenAI key is fetched from the environment variable (`os.getenv("OPENAI_API_KEY")`):
1. `backend/openai_client.py` (Line 7)
2. `backend/routes/config.py` (Line 50)
3. `backend/routes/langchain_create_agent.py` (Line 29)
4. `backend/domain_detector.py` (Line 9)

### Vercel Backend Link

To point your Vercel frontend to the Render backend, configure it here:
- **File:** `frontend/.env`
- Add: `VITE_API_URL=https://<your-render-backend-url>.onrender.com`

*Note: The system uses **only** standard OpenAI and **MongoDB**. OpenRouter and SQLite are not used.*

---

## 2. Deploying the Backend to Render

Since the backend is a Python (FastAPI/Bottle) server, **Render** is the best choice.

### Steps:
1. Push your repository to **GitHub**.
2. Log into [Render.com](https://render.com) and create a new **Web Service**.
3. Connect your GitHub repository.
4. **Configuration Settings**:
   - **Root Directory:** leave blank (use the root of the repository)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables**:
   Under the "Environment" section in Render, add:
   - `MONGO_URI` = `mongodb+srv://...`
   - `OPENAI_API_KEY` = `sk-...`
6. Click **Deploy**. Render will give you a backend URL (e.g., `https://agent4plc-backend.onrender.com`). *Copy this URL.*

---

## 3. Deploying the Frontend to Vercel

The frontend (React/Vite) can easily be deployed to **Vercel**.

### Steps:
1. Log into [Vercel.com](https://vercel.com) and click **Add New Project**.
2. Import your GitHub repository.
3. **Configuration Settings**:
   - **Framework Preset:** `Vite` or `React` (Vercel usually detects this automatically).
   - **Root Directory:** Edit this and select the `frontend` folder.
4. **Environment Variables**:
   You need to point the frontend to your newly deployed Render backend. Add standard `VITE_` env variables if applicable:
   - `VITE_API_URL` = `https://agent4plc-backend.onrender.com` (Your Render URL).
5. Click **Deploy**. Your frontend will be live in minutes.
