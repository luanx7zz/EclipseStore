import json
import os

def _normalize(value):
    if isinstance(value, list):
        return [str(x) for x in value if str(x).strip()]
    if isinstance(value, dict):
        return [str(k) for k, v in value.items() if v]
    if isinstance(value, (str, int)):
        return [str(value)]
    return []

def _load_config_perms():
    paths = [
        "config.json",
        "database/settings/permissoes.json",
        "database/settings/permissions.json",
        "database/perms.json",
    ]

    result = []

    for path in paths:
        if not os.path.exists(path):
            continue

        try:
            data = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue

        if isinstance(data, dict):
            if isinstance(data.get("bot"), dict):
                result += _normalize(data["bot"].get("perms"))
                result += _normalize(data["bot"].get("owner"))
            result += _normalize(data.get("perms"))
            result += _normalize(data.get("permissions"))
            result += _normalize(data.get("owners"))
            result += _normalize(data.get("admins"))
        else:
            result += _normalize(data)

    return list(dict.fromkeys(result))

perms = _load_config_perms()

async def check(user_id):
    global perms
    if not perms:
        perms = _load_config_perms()
    return str(user_id) in perms
