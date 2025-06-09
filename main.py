from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import query_routers
from app.routers import auth_routers
from dotenv import load_dotenv
import os
from contextlib import asynccontextmanager
from app.db.db import init_db_pool, close_db_pool

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    yield
    await close_db_pool()

app = FastAPI(lifespan=lifespan)

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
origins = [
    "https://query-nl.vercel.app",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_routers.router, prefix="/query", tags=["query"])
app.include_router(auth_routers.router, prefix="/auth", tags=["Authentication"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
