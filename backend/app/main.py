from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, anime_list, mal_import

app = FastAPI(title="Arcanum API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(anime_list.router)
app.include_router(mal_import.router)

@app.get("/")
async def root():
    return {"message": "Arcanum API is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}