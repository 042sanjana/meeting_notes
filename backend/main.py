from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.meeting_routes import router

app = FastAPI(
    title="AI Meeting Notes Generator"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router)

@app.get("/")
def home():
    return {
        "message": "AI Meeting Notes Generator API Running"
    }