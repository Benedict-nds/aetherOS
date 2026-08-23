from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.db import SessionLocal, engine
from app.core.responses import error_response, success_response
from app.core.seed import seed_demo_user
from app.modules.auth.router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        seed_demo_user(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.app_name,
    description="AI-native pharmacy operations platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["auth"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "success" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=getattr(exc, "headers", None),
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.get("/health")
def health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return success_response(
            data={
                "status": "ok",
                "service": "aetherqore-backend",
                "version": "0.1.0",
                "database": "connected",
            },
            message="Service is healthy",
        )
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content=error_response(
                message="Service unhealthy",
                errors=[str(exc)],
            ),
        )
