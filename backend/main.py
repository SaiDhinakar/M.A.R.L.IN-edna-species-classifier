from fastapi import FastAPI
from src.api.v1.auth_api import router as auth_router

app = FastAPI(
    title="eDNA Species Classifier Backend",
    description="Backend API for eDNA Species Classifier",
    version="1.0.0",
)

app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the eDNA Species Classifier Backend API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)