from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os

from app.routes import cases, health, audit, screening, documents, model, dashboard


class Settings(BaseSettings):
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    mongodb_database: str = os.getenv("MONGODB_DATABASE", "securedoc")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

app = FastAPI(
    title="SecureDoc AI API",
    description="AI-Based Fake Identity and Document Screening System",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router, prefix="/api", tags=["Cases"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(audit.router, prefix="/api", tags=["Audit"])
app.include_router(screening.router, prefix="/api/screen", tags=["Screening"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(model.router, prefix="/api", tags=["Model"])


@app.on_event("startup")
async def startup():
    print("[SecureDoc] Starting up...")
    if settings.mongodb_uri:
        try:
            client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
            client.admin.command("ping")
            app.state.mongodb_client = client
            app.state.mongodb_db = client[settings.mongodb_database]
            print("[SecureDoc] MongoDB Atlas connected successfully")
        except Exception as e:
            print(f"[SecureDoc] WARNING: MongoDB Atlas connection failed: {e}. Running in mock mode.")
            app.state.mongodb_client = None
            app.state.mongodb_db = None
    else:
        print("[SecureDoc] WARNING: MONGODB_URI not set. Running in mock mode.")
        app.state.mongodb_client = None
        app.state.mongodb_db = None


@app.on_event("shutdown")
async def shutdown():
    if hasattr(app.state, "mongodb_client") and app.state.mongodb_client is not None:
        app.state.mongodb_client.close()
        print("[SecureDoc] MongoDB connection closed")


@app.get("/")
async def root():
    return {"message": "SecureDoc AI API", "status": "running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SecureDoc AI Backend"}
