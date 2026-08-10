from fastapi import FastAPI

app = FastAPI(
    title="AetherQore Pharmacy OS",
    description="AI-native pharmacy operations platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "aetherqore-backend",
        "version": "0.1.0",
    }