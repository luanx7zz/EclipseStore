"""
Sistema de sugestões da loja.
"""
from functions.database import database as db
import logging
logger = logging.getLogger("eclipse_store.loja.preferences.sugestoes")


class SugestoesManager:
    @staticmethod
    def get_config() -> dict:
        prefs = db.get_document("loja_preferences") or {}
        return prefs.get("sugestoes", {"enabled": False, "channel_id": None})

    @staticmethod
    def is_enabled() -> bool:
        return SugestoesManager.get_config().get("enabled", False)
