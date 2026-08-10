from fastapi import FastAPI

from routers import recommendations

app = FastAPI(title="Wardrobe Stylist API")

app.include_router(recommendations.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}