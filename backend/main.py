from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database.db
from routes.auth_routes import router as auth_router

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
app.include_router(auth_router)

@app.get("/")
def home():
    return {
        "message": "AI Meeting Notes Generator API Running"
    }