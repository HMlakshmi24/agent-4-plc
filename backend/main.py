from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import home, login, plc_to_st, download

app = FastAPI(title="Agent4PLC Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(home.router)
app.include_router(login.router)
app.include_router(plc_to_st.router)
app.include_router(download.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

