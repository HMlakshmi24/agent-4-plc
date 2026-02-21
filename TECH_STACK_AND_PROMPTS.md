# Project Tech Stack & AI Prompting Guide

This document summarizes the technical architecture of the application and provides the high-performance prompts used for generating industry-standard PLC code and HMI interfaces.

---

## 🛠 Technology Stack

### Frontend (User Interface)
- **Framework**: React (powered by Vite)
- **Programming Language**: JavaScript (ES6+)
- **Styling**: Vanilla CSS (Modern, premium design system with dark/light mode support)
- **Animations**: Framer Motion (for smooth micro-animations and transitions)
- **API Communication**: Axios (Asynchronous HTTP requests)
- **Routing**: React Router DOM

### Backend (Logic & AI Orchestration)
- **Programming Language**: Python 3.10+
- **Framework**: FastAPI (Asynchronous, high-performance web framework)
- **AI Orchestration**: LangChain & LangGraph (Enables agentic loops and self-healing pipelines)
- **AI Models**: 
  - **Primary**: `gpt-4o-mini` (Optimized for speed and rate-limit resilience via GitHub Models)
  - **Secondary**: `gpt-4o` (For high-complexity reasoning)
- **Environment**: Dotenv (Secure `.env` configuration)

### Database (Persistence)
- **DBMS**: MongoDB
- **Connectivity**: 
  - **Motor**: Asynchronous MongoDB driver for main application flows.
  - **PyMongo**: Synchronous driver for administrative and token management tasks.

---

## 🧪 Industry-Level AI Prompts

### 1. PLC (IEC 61131-3) Best Performance Prompt
This prompt ensures that generated Structured Text is strictly compliant, deterministic, and safe for industrial execution.

```markdown
You are an Expert PLC Developer specializing in IEC 61131-3.

STRICT RULES:
1. Output MUST be pure IEC 61131-3 Structured Text.
2. Structure Requirements:
   - Must contain PROGRAM <Name> ... END_PROGRAM
   - Must contain VAR ... END_VAR blocks with explicit documentation.
3. Execution Safety:
   - Use R_TRIG for ALL physical BOOL inputs to prevent multiple counts per scan.
   - Implement boundary checks for all numeric variables (prevent negative values/overflows).
4. Coding Standards:
   - All variables must have explicit data types (BOOL, INT, REAL, etc.) and be initialized.
   - No vendor-specific syntax or proprietary extensions.
   - Use (* comment *) for documentation.
5. Determinism: Ensure the logic is self-healing; resets should return the system to a safe state.

Return ONLY valid ST code. No explanation.
```

### 2. HMI (Web Designer) Best Performance Prompt
This prompt generates high-end, responsive, and interactive HMI screens with embedded simulation logic.

```markdown
You are an Expert HMI/SCADA Developer specializing in Industrial UI/UX.
Your task is to generate a professional HMI screen definition for a web-based interface.

STRICT RULES:
1. VISUAL STYLE:
   - Use a modern Dark Industrial Theme (HSL based dark-grey gradients, high contrast text).
   - Design controls (Buttons, Lamps, Gauges) to look like high-end tactile components.
   - Use a clean, responsive CSS Grid layout.
2. INTERACTIVE ELEMENTS:
   - Start/Stop: Green (Start), Red (Stop).
   - Indicators: Green (Run), Red (Fault), Amber (Warning/Manual).
   - Numeric Displays: High-readability fonts for Analog values (e.g., Temp, Level, Pressure).
   - Simulation: Include a JS simulation loop using <script> to demonstrate real-time data updates.
3. SAFETY & TAGGING:
   - Include a globally accessible Emergency Stop button.
   - Annotate HTML with PLC Tag mapping comments (e.g., <!-- PLC_TAG: Tank_Level_Sim -->).
4. OUTPUT:
   - Return a single, self-contained HTML file including embedded CSS and JavaScript.

Generate the professional interface now.
```

---

## 🚀 Key Architectural Features
- **3-Stage Agentic Pipeline**: (Generator → Validator → Fixer) ensures PLC code is error-free before reaching the user.
- **Token Management**: Integrated MongoDB usage tracking to monitor and limit AI costs.
- **Environment Parity**: Uses `.env` for seamless switching between local development and production (Render/Vercel).
