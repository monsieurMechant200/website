import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.utils.supabase_client import db_manager
from app.utils.scheduler import scheduler
from app.routes import auth, orders, messages, gallery, admin, appointments


# =========================
# LOGGING CONFIG
# =========================

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# =========================
# LIFESPAN
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # -------- STARTUP --------
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize database (SYNC)
    logger.info("Initializing database...")
    db_manager.initialize_database()

    # Start scheduler if enabled
    scheduler_task = None
    if settings.SCHEDULER_ENABLED:
        logger.info("Starting scheduler...")
        scheduler_task = asyncio.create_task(scheduler.start())

    yield

    # -------- SHUTDOWN --------
    logger.info("Shutting down application...")

    if scheduler_task:
        scheduler.stop()
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
        logger.info("Scheduler stopped")


# =========================
# FASTAPI APP
# =========================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for DATAIKÔS Student Platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# =========================
# STATIC FILES
# =========================

app.mount(
    "/uploads",
    StaticFiles(directory=settings.UPLOAD_DIR),
    name="uploads",
)


# =========================
# ROUTERS
# =========================

app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(messages.router)
app.include_router(gallery.router)
app.include_router(admin.router)
app.include_router(appointments.router)


# =========================
# GLOBAL EXCEPTION HANDLER
# =========================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Uncaught exception", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else None,
        },
    )


# =========================
# HEALTH & INFO
# =========================

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else None,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/api/info")
def api_info():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "DATAIKÔS Student Platform API",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "endpoints": {
            "auth": "/api/auth",
            "orders": "/api/orders",
            "messages": "/api/messages",
            "gallery": "/api/gallery",
            "admin": "/api/admin",
            "appointments": "/api/appointments",
        },
    }


# =========================
# EXAMPLE PROTECTED ROUTE
# =========================

@app.get("/api/protected")
def protected_endpoint(
    user: Dict[str, Any] = Depends(auth.auth_handler.get_current_user)
):
    return {
        "message": f"Hello {user.get('username')}!",
        "user_id": user.get("id"),
        "is_admin": user.get("is_admin", False),
    }
