import json
import os

def _load_config_perms():
    paths = [
        "config.json",
        "database/settings/permissoes.json",
        "database/settings/permissions.json",
        "database/perms.json",
    ]

    for path in paths:
        if not os.path.exists(path):
            continue

        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue

        if isinstance(data, dict):
            if "bot" in data and isinstance(data["bot"], dict):
                value = data["bot"].get("perms") or data["bot"].get("owner")
            else:
                value = data.get("perms") or data.get("permissions") or data.get("owners") or data.get("admins")
        else:
            value = data

        if isinstance(value, list):
            return [str(x) for x in value if str(x).strip()]
        if isinstance(value, dict):
            return [str(k) for k, v in value.items() if v]
        if isinstance(value, (str, int)):
            return [str(value)]

    return []

async def check(user_id):
    perms = _load_config_perms()
    return str(user_id) in perms
