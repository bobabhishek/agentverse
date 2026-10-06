import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.routes import health, chat, simulation, ledger, database, banking

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("fema.main")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} on {settings.HOST}:{settings.PORT}")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Frontend Origin: {settings.FRONTEND_ORIGIN}")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="FEMA Autonomous Rogue Agent Guardrail Testing Simulation Backend",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
allowed_origins = [
    settings.FRONTEND_ORIGIN.rstrip("/"),
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
# Deduplicate
allowed_origins = list(set(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred during FEMA guardrail simulation"}
    )

# Include routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(simulation.router)
app.include_router(ledger.router)
app.include_router(database.router)
app.include_router(banking.router)
