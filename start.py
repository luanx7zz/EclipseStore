"""
Eclipse Store Bot — Entrypoint principal seguro.

Uso:
    python start.py

Variáveis de ambiente recomendadas:
    BOT_TOKEN   — token do bot Discord
    MONGO_URL   — URL do MongoDB
    BOT_ID      — ID da aplicação/bot
    OWNER_ID    — ID do dono
    SERVER_ID   — ID do servidor principal
    API_URL     — URL da API/manager, se usar saveConfig=True
"""
import json
import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def load_dotenv() -> None:
    """Carrega .env simples em desenvolvimento local, sem sobrescrever Secrets do ambiente."""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists() or path.stat().st_size == 0:
        return default.copy()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"❌ JSON inválido em {path}: {exc}")
        sys.exit(1)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")


def patch_configs() -> None:
    """Injeta Secrets/ENV nos arquivos que o bot legado espera ler."""
    bot_token = os.environ.get("BOT_TOKEN", "").strip()
    mongo_url = (os.environ.get("MONGO_URL") or os.environ.get("MONGODB_URL") or "").strip()
    bot_id = os.environ.get("BOT_ID", "").strip()
    owner_id = os.environ.get("OWNER_ID", "").strip()
    server_id = os.environ.get("SERVER_ID", "").strip()
    api_url = os.environ.get("API_URL", "http://localhost:22222").strip()

    missing = []
    if not bot_token:
        missing.append("BOT_TOKEN")
    if not mongo_url:
        missing.append("MONGO_URL")
    if missing:
        print("❌ ERRO: Secrets obrigatórias ausentes: " + ", ".join(missing))
        print("   Na Discloud, adicione essas chaves nas variáveis de ambiente/Secrets da aplicação.")
        sys.exit(1)

    config_path = BASE_DIR / "config.json"
    default_config = {
        "saveConfig": False,
        "botToken": "",
        "apiURL": api_url,
        "botID": bot_id or "local_bot",
        "version": "1.0.0",
        "bot": {
            "token": "",
            "owner": owner_id,
            "id": bot_id or "local_bot",
            "perms": 8,
            "server": server_id,
        },
    }
    config = _read_json(config_path, default_config)

    config.setdefault("saveConfig", False)
    config["botToken"] = bot_token
    config["apiURL"] = api_url
    config["botID"] = bot_id or config.get("botID") or "local_bot"
    config.setdefault("bot", {})
    config["bot"]["token"] = bot_token
    config["bot"]["id"] = bot_id or config["bot"].get("id") or config["botID"]
    config["bot"]["owner"] = owner_id or config["bot"].get("owner", "")
    config["bot"]["server"] = server_id or config["bot"].get("server", "")
    config["bot"].setdefault("perms", 8)
    _write_json(config_path, config)

    mongo_path = BASE_DIR / "configs" / "config_mongo.json"
    mongo_config = _read_json(mongo_path, {"mongoURL": "", "databaseName": "sync_bots"})
    mongo_config["mongoURL"] = mongo_url
    mongo_config.setdefault("databaseName", os.environ.get("MONGO_DATABASE", "sync_bots"))
    _write_json(mongo_path, mongo_config)

    print("✅ Configurações carregadas com sucesso!")
    print(f"   Bot ID  : {config.get('botID', '?')}")
    print(f"   Owner   : {config.get('bot', {}).get('owner', '?')}")
    print(f"   Server  : {config.get('bot', {}).get('server', '?')}")


def install_asyncio_error_handler(bot_module) -> None:
    """Registra handler para exceções perdidas em tasks asyncio."""
    import asyncio
    import logging
    import traceback

    def _asyncio_exception_handler(loop, context):
        exc = context.get("exception")
        if isinstance(exc, asyncio.CancelledError):
            return
        if exc is None:
            logging.getLogger("eclipse_store").error(
                "[asyncio] Erro sem exceção: %s", context.get("message", "?")
            )
            return
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logging.getLogger("eclipse_store").error("[asyncio] Exceção não capturada em task:\n%s", tb)

    bot_module._asyncio_exception_handler = _asyncio_exception_handler


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    load_dotenv()
    patch_configs()

    from functions.logger import setup_logging

    setup_logging(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    import bot as bot_module

    install_asyncio_error_handler(bot_module)

    try:
        bot_module.bot.run(bot_module.token)
    finally:
        # Fecha sessão HTTP global de pagamentos, evitando "Unclosed client session".
        try:
            import asyncio
            from functions.payments.api_client import close_api_client

            asyncio.run(close_api_client())
        except Exception:
            pass
