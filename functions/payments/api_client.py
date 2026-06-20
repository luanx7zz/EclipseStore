"""
Cliente para a API de Pagamentos.

Correções:
- URL da API pode vir de PAY_API_URL/API_URL ou configs/config_api.json.
- Reutiliza uma sessão aiohttp por processo.
- Expõe close_api_client() para fechar a sessão no shutdown e evitar:
  "Unclosed client session" / "Unclosed connector".
"""
import os
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from functions.database import database as db


class PaymentAPIClient:
    """Cliente HTTP para API de Pagamentos."""

    def __init__(self):
        self.base_url = self._get_api_url()
        self.session: Optional[aiohttp.ClientSession] = None

    def _get_api_url(self) -> str:
        """Obtém URL da API por ENV primeiro, depois config local."""
        api_url = (
            os.environ.get("PAY_API_URL")
            or os.environ.get("API_URL")
            or ""
        ).strip()

        if not api_url:
            try:
                config = db.obter("configs/config_api.json") or {}
                api_url = str(config.get("api", "localhost:22222")).strip()
            except Exception:
                api_url = "localhost:22222"

        if not api_url.startswith(("http://", "https://")):
            api_url = f"http://{api_url}"

        return api_url.rstrip("/")

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Garante que a sessão HTTP existe e está aberta."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self) -> None:
        """Fecha a sessão HTTP."""
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None

    async def _post_json(self, path: str, payload: Dict[str, Any], timeout: int = 20) -> Dict[str, Any]:
        """Faz requisição POST para a API."""
        session = await self._ensure_session()
        url = f"{self.base_url}/api/v1/{path.lstrip('/')}"

        try:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                text = await resp.text()

                if resp.status >= 400:
                    raise RuntimeError(f"Erro na API ({resp.status}): {text}")

                try:
                    return await resp.json()
                except Exception as exc:
                    raise RuntimeError(f"Resposta inválida do servidor: {text[:300]}") from exc

        except asyncio.TimeoutError as exc:
            raise RuntimeError(f"Timeout ao conectar com API ({timeout}s)") from exc
        except aiohttp.ClientError as exc:
            raise RuntimeError(f"Erro de conexão com API: {exc}") from exc

    async def create_mp_payment(self, token_mp: str, value: float, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Cria pagamento Mercado Pago."""
        payload = {
            "token_mp": token_mp,
            "value": value,
        }

        if webhook_url:
            payload["webhook_url"] = webhook_url

        return await self._post_json("create-mp-payment", payload)

    async def check_mp_payment(self, token_mp: str, payment_id: str) -> Dict[str, Any]:
        """Verifica status de pagamento Mercado Pago."""
        return await self._post_json("check-mp-payment", {
            "token_mp": token_mp,
            "payment_id": payment_id,
        })


_api_client: Optional[PaymentAPIClient] = None


def get_api_client() -> PaymentAPIClient:
    """Obtém instância global do cliente."""
    global _api_client
    if _api_client is None:
        _api_client = PaymentAPIClient()
    return _api_client


async def close_api_client() -> None:
    """Fecha a sessão global, se existir."""
    global _api_client
    if _api_client is not None:
        await _api_client.close()
        _api_client = None


async def create_mp_payment_from_api(value: float, webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """Cria pagamento MP via API."""
    payment_configs = db.get_document("payment_configs") or {}
    mp_config = payment_configs.get("mercado_pago", {})
    token_mp = mp_config.get("access_token")

    if not token_mp:
        raise ValueError("Token do Mercado Pago não configurado")

    return await get_api_client().create_mp_payment(token_mp, value, webhook_url)


async def check_mp_payment_from_api(payment_id: str) -> Dict[str, Any]:
    """Verifica pagamento MP via API."""
    payment_configs = db.get_document("payment_configs") or {}
    mp_config = payment_configs.get("mercado_pago", {})
    token_mp = mp_config.get("access_token")

    if not token_mp:
        raise ValueError("Token do Mercado Pago não configurado")

    return await get_api_client().check_mp_payment(token_mp, payment_id)
