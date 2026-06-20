"""
Funções compartilhadas entre create_payment.py e check_payment.py.
Centraliza: URL da API, sanitização de erros, POST JSON, config, credenciais EfiBank.
"""
import aiohttp
import base64
import json
import re
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from functions.database import database as db

logger = logging.getLogger("eclipse_store.payments")


def _get_api_url() -> str:
    """Carrega URL da API de config_api.json"""
    try:
        config_path = Path(__file__).parent.parent.parent / "configs" / "config_api.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                api_url = config.get("api", "localhost:22222")
                if not api_url.startswith(("http://", "https://")):
                    api_url = f"http://{api_url}"
                return api_url.rstrip("/")
    except Exception as e:
        logger.warning(f"Erro ao carregar config_api.json: {e}")
    return "https://pay.syncapplications.com.br"


def _get_base_url() -> str:
    """Retorna BASE_URL dinamicamente (lê config a cada chamada, não em import)."""
    return f"{_get_api_url()}/api/v1"


def _sanitize_error_message(error_msg: str) -> str:
    """Remove informações técnicas de mensagens de erro para o usuário."""
    msg = str(error_msg)

    try:
        json_match = re.search(r'\{[^{}]*"mensagem"[^{}]*\}', msg, re.IGNORECASE)
        if json_match:
            data = json.loads(json_match.group(0))
            if isinstance(data, dict) and "mensagem" in data:
                return data["mensagem"]
    except Exception:
        pass

    try:
        json_match = re.search(r'\{[^{}]*"message"[^{}]*\}', msg, re.IGNORECASE)
        if json_match:
            data = json.loads(json_match.group(0))
            if isinstance(data, dict):
                msg_data = data.get("message")
                if isinstance(msg_data, dict) and "mensagem" in msg_data:
                    return msg_data["mensagem"]
                elif isinstance(msg_data, str):
                    return msg_data
    except Exception:
        pass

    msg = re.sub(r"https?://[^\s]+", "", msg)
    msg = re.sub(r"/api/v\d+/[^\s]+", "", msg)
    msg = re.sub(r"/api/[^\s]+", "", msg)
    msg = re.sub(r"^\d+\s+", "", msg)
    msg = re.sub(r"pay\.syncapplications\.com\.br[^\s]*", "", msg, flags=re.IGNORECASE)
    msg = re.sub(r"\s+", " ", msg)
    msg = re.sub(r"^:\s*", "", msg)
    msg = msg.strip()

    if not msg or len(msg) < 3:
        return "Erro ao processar pagamento. Verifique as configurações."
    return msg


async def _post_json(path: str, payload: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
    """Faz POST JSON para a API de pagamentos."""
    url = f"{_get_base_url()}/{path}"
    t = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=t) as session:
        async with session.post(url, json=payload) as resp:
            text = await resp.text()
            try:
                data = json.loads(text)
            except Exception:
                data = None
            if resp.status >= 400:
                sanitized_msg = _sanitize_error_message(text)
                raise RuntimeError(sanitized_msg)
            if data is None:
                raise RuntimeError("Resposta inválida do servidor")
            return data


def _load_config() -> dict:
    """Carrega configurações de pagamento do database."""
    return db.get_document("payment_configs") or {}


def _require(value: Optional[str], what: str) -> str:
    if not value:
        raise ValueError(f"Missing {what} in payment settings.")
    return value


def _efi_credentials() -> Dict[str, str]:
    """Carrega credenciais do EfiBank do database."""
    cfg = _load_config().get("efibank") or {}
    client_id = cfg.get("client_id") or cfg.get("client")
    client_secret = cfg.get("client_secret") or cfg.get("token")
    pix_key = cfg.get("pix_key")
    cert_file = cfg.get("cert_file")
    cert_b64: Optional[str] = None

    if cert_file and isinstance(cert_file, str) and cert_file.strip():
        cert_path = Path(cert_file)
        if cert_path.exists():
            try:
                data = cert_path.read_bytes()
                cert_b64 = base64.b64encode(data).decode("ascii")
            except Exception as e:
                logger.error(f"[Efi] Erro ao ler certificado: {e}")
                cert_b64 = None
        else:
            logger.warning(f"[Efi] Certificado não encontrado: {cert_file}")
    else:
        logger.warning("[Efi] Caminho do certificado não configurado")

    return {
        "client_id": _require(client_id, "Efi client_id"),
        "client_secret": _require(client_secret, "Efi client_secret"),
        "pix_key": _require(pix_key, "Efi pix_key"),
        "certificate": _require(
            cert_b64,
            "Efi certificate (.p12) — verifique se o arquivo existe no caminho configurado",
        ),
    }


__all__ = [
    "_get_api_url",
    "_get_base_url",
    "_sanitize_error_message",
    "_post_json",
    "_load_config",
    "_require",
    "_efi_credentials",
]
