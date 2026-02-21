# Agent4PLC - Setup & Deployment Guide

## Local Setup (Running Offline)

Steps to run the system locally on a new PC:

1. Open a terminal in the project folder.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Setup Environment Variables:
   Create a `backend/.env` file with the following keys:
   ```env
   # 1. MongoDB Connection (Required)
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/?retryWrites=true&w=majority
   
   # 2. OpenAI API Key (Required)
   OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY
   
   # 3. Optional: Host and Port
   PORT=8000
   HOST=0.0.0.0
   ```
4. Start the backend server:
   ```bash
   uvicorn backend.main:app --reload
   ```
5. Open the API docs:
   http://127.0.0.1:8000/docs
6. Use the `/offline/generate` endpoint for generation.

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
   - **Root Directory:** `backend` (Important!)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r ../requirements.txt`
   - **Start Command:** `uvicorn run_backend:app --host 0.0.0.0 --port $PORT` (Adjust based on your actual main entry file).
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
