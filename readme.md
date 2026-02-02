# Agent4PLC

A powerful, AI-driven assistant for PLC code generation and HMI design, featuring a premium modern UI and strict IEC 61131-3 compliance.

## Project Overview

Agent4PLC is a full-stack application that leverages LLMs to generate industrial control code (Structured Text, Ladder Logic, etc.) and HMI interfaces.

### Key Features
-   **AI Code Generation**: Transforms plain text requirements into valid PLC code.
-   **Multi-Language Support**: ST, LD, FBD, SFC, IL.
-   **HMI Generation**: Creates ISA-101 compliant HTML interfaces.
-   **Premium UI**: "Black Design" default with Light/Dark theme toggling.
-   **Centralized Output**: All generated files are stored in `backend/plc`.

## Folder Structure

The project is organized to ensure clarity and maintainability.

```
agent-4-plc/
├── backend/                # FastAPI Backend
│   ├── plc/                # [NEW] Output directory for ALL generated files
│   ├── routes/             # API Endpoints
│   ├── main.py             # Entry point
│   └── .env                # Configuration
├── frontend/               # Vite + React Frontend
│   ├── public/
│   │   └── plc/            # Publicly accessible PLC assets
│   ├── src/
│   │   ├── components/     # UI Components
│   │   ├── context/        # React Context (Theme, Auth)
│   │   └── pages/          # Full pages
│   └── tailwind.config.js  # Styling config
└── README.md               # This file
```

## Setup & Running

### Prerequisites
-   Python 3.10+
-   Node.js 18+
-   MongoDB (local or remote)

### Backend
1.  Navigate to `backend/`:
    ```bash
    cd backend
    ```
2.  Install dependencies (if not already):
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure `.env`:
    Ensure `PLC_OUTPUT_DIR=backend/plc` is set.
4.  Run the server:
    ```bash
    python main.py
    ```
    *Server runs on `http://localhost:8001`*

### Frontend
1.  Navigate to `frontend/`:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Start the development server:
    ```bash
    npm run dev
    ```
    *App runs on `http://localhost:5173`*

## Configuration

**Output Directory**:
The backend saves all generated files to the path specified in `backend/.env`.
```env
PLC_OUTPUT_DIR=backend/plc
```
Changing this path allows you to redirect outputs to a network drive or another folder.

## Theming
The application defaults to a **Premium Black** design. Users can toggle between **Light** and **Dark** modes using the sun/moon icon in the navigation bar. 
-   **Dark Mode**: Optimized for low-light control room environments (Default).
-   **Light Mode**: High contrast for bright environments.

