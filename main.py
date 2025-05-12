from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import query_routers

app = FastAPI()
app.include_router(query_routers.router, prefix="/query", tags=["query"])
CORSMiddleware(
    app,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, log_level="info", reload=True)