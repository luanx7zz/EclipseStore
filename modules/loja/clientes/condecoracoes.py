"""
Condecoraçoes de clientes — cargos especiais por nível de compra.
"""
from functions.database import database as db
import logging
logger = logging.getLogger("eclipse_store.loja.clientes.condecoracoes")


class Condecoracoes:
    @staticmethod
    def get_config() -> dict:
        customers_data = db.get_document("loja_customers") or {}
        return customers_data.get("decorations", {})

    @staticmethod
    def get_roles() -> list:
        return Condecoracoes.get_config().get("roles", [])

    @staticmethod
    def get_role_for_value(total_spent: float) -> int | None:
        roles = Condecoracoes.get_roles()
        eligible = [r for r in roles if total_spent >= r.get("min_value", 0)]
        if not eligible:
            return None
        return int(sorted(eligible, key=lambda r: r["min_value"], reverse=True)[0]["role_id"])
