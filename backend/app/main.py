from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, chat, progress, auth, speech

app = FastAPI(
    title="Agent IA - Apprentissage du Français",
    version="0.1.0",
    description="API backend pour l'agent conversationnel d'apprentissage du français",
)

# CORS pour permettre au frontend Next.js d'appeler l'API en local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(progress.router)
app.include_router(speech.router)


@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API de l'agent IA d'apprentissage du français"}
