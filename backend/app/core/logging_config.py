"""
Logging structuré (Phase 8).

En développement, des logs texte lisibles sont plus pratiques. En
production, des logs JSON (une ligne = un objet JSON) sont ce qu'attendent
la plupart des systèmes d'agrégation de logs (ELK, Datadog, CloudWatch,
Loki...) pour pouvoir filtrer/chercher efficacement.

Contrôlé par LOG_FORMAT dans .env : "json" ou "text" (défaut "text").
"""
import json
import logging
import os
import sys


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    log_format = os.getenv("LOG_FORMAT", "text").lower()
    handler = logging.StreamHandler(sys.stdout)

    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]

    # httpx/httpcore sont bavards en INFO (une ligne par requête HTTP
    # sortante vers le LLM) : utile en dev, bruyant en prod.
    if log_format == "json":
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
