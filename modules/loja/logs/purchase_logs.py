import json, os
from datetime import datetime

class PurchaseLogsSystem:
    def __init__(self, bot=None):
        self.bot = bot
        self.path = "database/loja/purchase_logs.json"
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            json.dump([], open(self.path, "w", encoding="utf-8"))

    def _load(self):
        try:
            return json.load(open(self.path, encoding="utf-8"))
        except Exception:
            return []

    def _save(self, data):
        json.dump(data, open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    async def create_log(self, *args, **kwargs):
        logs = self._load()
        log = {
            "id": kwargs.get("id") or kwargs.get("purchase_id") or str(int(datetime.utcnow().timestamp())),
            "created_at": datetime.utcnow().isoformat(),
            "user_id": str(kwargs.get("user_id") or kwargs.get("buyer_id") or ""),
            "product_name": str(kwargs.get("product_name") or kwargs.get("product") or "Produto"),
            "price": kwargs.get("price") or kwargs.get("value") or kwargs.get("amount") or 0,
            "status": kwargs.get("status") or "approved",
            "payment_method": kwargs.get("payment_method") or kwargs.get("method") or "",
            "raw": {k: str(v) for k, v in kwargs.items()}
        }
        logs.append(log)
        self._save(logs)
        return log

    async def log_purchase(self, *args, **kwargs):
        return await self.create_log(*args, **kwargs)

    async def send_purchase_log(self, *args, **kwargs):
        return await self.create_log(*args, **kwargs)
