// src/config/api.js
// Works for Create-React-App (REACT_APP_*) and falls back to localhost for dev.
export const API = import.meta.env.VITE_API_URL || "http://localhost:8001";