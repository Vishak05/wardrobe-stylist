from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routers import recommendations
from routers.ingestion import router as ingestion_router

app = FastAPI(title="Wardrobe Stylist API")

app.include_router(recommendations.router)
app.include_router(ingestion_router)
app.mount("/media", StaticFiles(directory="media"), name="media")

@app.get("/health")
async def health_check():
    return {"status": "ok"}