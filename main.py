from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import query_routers
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
origins = [
    frontend_url
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_routers.router, prefix="/query", tags=["query"])
