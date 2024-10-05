# app/main.py
from fastapi import FastAPI
from app.routes import recommendations

app = FastAPI()

# Include recommendations routes
app.include_router(recommendations.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
