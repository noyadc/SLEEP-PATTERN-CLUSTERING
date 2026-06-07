from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import analytics, auth, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Sleep Pattern Analytics API",
    description="Full-stack sleep clustering and lifestyle analytics platform",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {"message": "Sleep Pattern Analytics API", "docs": "/docs", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
