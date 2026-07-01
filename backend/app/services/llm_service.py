"""
Service responsable de la génération de réponses conversationnelles
et des corrections grammaticales via un LLM (GPT, Claude, etc.).

À implémenter :
- generate_reply(message, niveau_cecrl, historique) -> str
- correct_message(message) -> dict (erreurs détectées + explication)
"""

# TODO: importer le client de l'API LLM choisi (ex: openai, anthropic)


def generate_reply(message: str, niveau_cecrl: str = "A1") -> str:
    raise NotImplementedError("À connecter à l'API du LLM")


def correct_message(message: str) -> dict:
    raise NotImplementedError("À connecter à l'API du LLM")
