"""
Integração com Pollinations AI — gratuito, sem chave de API.
Usa semáforo global (1 req simultânea) para não estourar a fila do IP.
"""
import aiohttp
import asyncio
import logging

logger = logging.getLogger("eclipse_store.ai")

POLLINATIONS_URL = "https://text.pollinations.ai/"

_DEFAULT_SYSTEM = (
    "Você é um assistente prestativo chamado EclipseAI. "
    "Responda de forma clara, objetiva e em português do Brasil."
)

# ── Rate-limit protection ────────────────────────────────────────────────────
# Pollinations limita 1 request em fila por IP no tier gratuito.
# Semáforo garante execução serializada; evita 429.
_SEMAPHORE = asyncio.Semaphore(1)

# Modelos para tentar em ordem
_MODELS = ["openai", "mistral", "claude-hybridspace"]


async def chamar_ia(
    conteudo: str,
    module_name: str = "IA",
    system_prompt: str = None,
    model: str = "openai",
    timeout: int = 30,
) -> str:
    """Chama Pollinations AI. Retorna resposta ou '' em caso de falha."""
    if not conteudo or not conteudo.strip():
        return ""
    messages = [
        {"role": "system", "content": system_prompt or _DEFAULT_SYSTEM},
        {"role": "user",   "content": conteudo.strip()},
    ]
    return await _call(messages, module_name, model, timeout)


async def chamar_ia_com_contexto(
    mensagens: list,
    module_name: str = "IA",
    system_prompt: str = None,
    model: str = "openai",
    timeout: int = 30,
) -> str:
    """Chama Pollinations com histórico completo de mensagens."""
    messages = [{"role": "system", "content": system_prompt or _DEFAULT_SYSTEM}]
    for m in mensagens:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": str(content)})
    return await _call(messages, module_name, model, timeout)


async def _call(messages: list, module_name: str, preferred_model: str, timeout: int) -> str:
    """Faz a chamada serializada à API com retry e fallback de modelo."""
    models_to_try = [preferred_model] + [m for m in _MODELS if m != preferred_model]

    async with _SEMAPHORE:
        for model in models_to_try:
            result = await _single_attempt(messages, module_name, model, timeout)
            if result:
                return result
            # Pequeno delay entre modelos para não sobrecarregar
            await asyncio.sleep(1)

    logger.warning(f"[{module_name}] Todos os modelos falharam — sem resposta da IA.")
    return ""


async def _single_attempt(
    messages: list,
    module_name: str,
    model: str,
    timeout: int,
    max_retries: int = 3,
) -> str:
    """Tenta um modelo com retry exponencial em caso de 429/timeout."""
    payload = {"model": model, "messages": messages, "jsonMode": False, "seed": -1}

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    POLLINATIONS_URL,
                    json=payload,
                    headers={"Content-Type": "application/json", "Accept": "text/plain"},
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    if resp.status == 200:
                        text = (await resp.text()).strip()
                        if text:
                            logger.debug(f"[{module_name}] modelo={model} OK ({len(text)} chars)")
                            return text
                        logger.warning(f"[{module_name}] modelo={model} resposta vazia")
                        return ""

                    if resp.status == 429:
                        wait = 5 * (2 ** attempt)   # 5s, 10s, 20s
                        body = await resp.text()
                        logger.warning(
                            f"[{module_name}] modelo={model} rate-limit (429) — "
                            f"aguardando {wait}s (tentativa {attempt+1}/{max_retries}). {body[:120]}"
                        )
                        if attempt < max_retries - 1:
                            await asyncio.sleep(wait)
                        continue

                    body = await resp.text()
                    logger.warning(f"[{module_name}] modelo={model} HTTP {resp.status}: {body[:200]}")
                    return ""

        except asyncio.TimeoutError:
            logger.warning(f"[{module_name}] modelo={model} timeout após {timeout}s (tentativa {attempt+1})")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
        except aiohttp.ClientError as e:
            logger.warning(f"[{module_name}] modelo={model} conexão: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"[{module_name}] modelo={model} inesperado: {type(e).__name__}: {e}")
            return ""

    return ""
