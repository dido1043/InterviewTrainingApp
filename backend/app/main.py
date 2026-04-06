from fastapi import FastAPI
from fastapi.responses import JSONResponse
from api.endpoints import router

app = FastAPI(
    title="Interview Training Application",
    description="A FastAPI application for interview training",
    version="1.0.0"
)

app.include_router(router, prefix="/api", tags=["analysis"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
