from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Interview Training Application",
    description="A FastAPI application for interview training",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Welcome to CourseWorkApp!"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
