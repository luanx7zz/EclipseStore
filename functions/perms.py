import json
import os

class PermsManager:
    def __init__(self):
        self.paths = [
            "config.json",
            "database/settings/permissoes.json",
            "database/settings/permissions.json",
            "database/perms.json",
        ]

    def _normalize(self, value):
        if isinstance(value, list):
            return [str(x) for x in value if str(x).strip()]
        if isinstance(value, dict):
            return [str(k) for k, v in value.items() if v]
        if isinstance(value, (str, int)):
            return [str(value)]
        return []

    def load(self):
        result = []

        for path in self.paths:
            if not os.path.exists(path):
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            if isinstance(data, dict):
                bot = data.get("bot")
                if isinstance(bot, dict):
                    result += self._normalize(bot.get("perms"))
                    result += self._normalize(bot.get("owner"))

                for key in ("perms", "permissions", "owners", "admins"):
                    result += self._normalize(data.get(key))
            else:
                result += self._normalize(data)

        return list(dict.fromkeys(result))

    async def check(self, user_id):
        return str(user_id) in self.load()

    def __iter__(self):
        return iter(self.load())

    def __contains__(self, user_id):
        return str(user_id) in self.load()

perms = PermsManager()

async def check(user_id):
    return await perms.check(user_id)
