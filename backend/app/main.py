from fastapi import FastAPI
from sqlalchemy import text

from app.core.db import engine
from app.core.config import settings
from app.core.responses import success_response, error_response
from fastapi.responses import JSONResponse

app = FastAPI(
    title=settings.app_name, 
    description="AI-native pharmacy operations platform", 
    version="0.1.0"
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
                content=error_response(message="Service unhealthy", errors=[str(exc)]),
        )
