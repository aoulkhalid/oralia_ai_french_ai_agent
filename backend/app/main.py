import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.routers import (
    health,
    chat,
    progress,
    auth,
    speech,
    scenarios,
    exercises,
    teacher,
    billing,
)

configure_logging()
logger = logging.getLogger("app.main")

app = FastAPI(
    title="Agent IA - Apprentissage du Français",
    version="0.1.0",
    description="API backend pour l'agent conversationnel d'apprentissage du français",
)

# CORS : origines autorisées lues depuis CORS_ORIGINS (voir .env), pas
# codées en dur, pour pouvoir pointer vers un domaine de prod sans
# toucher au code.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """
    En-têtes de sécurité de base (Phase 8). Une API JSON pure n'a pas
    besoin de toute la panoplie d'en-têtes d'une app web classique (pas
    de CSP complexe ici puisqu'il n'y a pas de HTML servi), mais ces
    quelques en-têtes protègent contre des scénarios d'attaque réels
    (sniffing MIME, clickjacking si l'API est un jour embarquée, downgrade
    HTTP) à coût nul.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    # HSTS : n'a de sens que derrière HTTPS (reverse proxy en prod) ; en
    # dev sur http://localhost ce header est simplement ignoré par le
    # navigateur, donc inoffensif de le laisser toujours actif.
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Filet de sécurité : toute exception non gérée renvoie un 500 JSON
    propre (jamais de stack trace exposée au client) et est loguée pour
    diagnostic côté serveur."""
    logger.exception("Erreur non gérée sur %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Une erreur interne est survenue."},
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(progress.router)
app.include_router(speech.router)
app.include_router(scenarios.router)
app.include_router(exercises.router)
app.include_router(teacher.router)
app.include_router(billing.router)


@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API de l'agent IA d'apprentissage du français"}
