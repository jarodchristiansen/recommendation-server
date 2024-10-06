# app/main.py
from fastapi import FastAPI
from app.routes import recommendations

app = FastAPI()

# Include recommendations routes
app.include_router(recommendations.router)

@app.get("/")
@app.head('/')
async def root():
    return {"message": "Hello World"}
