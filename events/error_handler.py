"""
Tratamento global de erros — captura TODAS as exceções não tratadas.
Impede crashes do bot e registra tudo com logging estruturado.
"""
import traceback
import logging
import asyncio
import sys
import os

import disnake
from disnake.ext import commands

logger = logging.getLogger("eclipse_store.error_handler")

_COLOR_ERROR = 0xe74c3c
_COLOR_WARN = 0xf39c12


def _is_silent(error: Exception) -> bool:
    cause = getattr(error, "original", error)
    if isinstance(cause, (commands.CommandNotFound, commands.CheckFailure)):
        return True
    if isinstance(cause, disnake.errors.InteractionTimedOut):
        return True
    if isinstance(cause, disnake.NotFound):
        return True
    if isinstance(cause, disnake.errors.HTTPException):
        if cause.code in (10062, 10008) or cause.status == 404:
            return True
    if isinstance(cause, asyncio.CancelledError):
        return True
    return False


async def _try_respond(inter: disnake.Interaction, msg: str) -> None:
    embed = disnake.Embed(description=f"❌ {msg}", color=_COLOR_ERROR)
    try:
        if hasattr(inter, "response") and not inter.response.is_done():
            await inter.response.send_message(embed=embed, ephemeral=True)
        elif hasattr(inter, "followup"):
            await inter.followup.send(embed=embed, ephemeral=True)
    except Exception:
        pass


def _log_error(context: str, cause: Exception) -> None:
    tb = "".join(traceback.format_exception(type(cause), cause, cause.__traceback__))
    logger.error(f"[{context}] Exceção não tratada:\n{tb}")


async def _try_send_error_webhook(content: str) -> None:
    """Envia erro crítico para webhook configurado (opcional)."""
    try:
        from functions.database import database as db
        config = db.get_document("bot_config") or {}
        webhook_url = os.environ.get("ERROR_WEBHOOK_URL") or config.get("error_webhook_url")
        if not webhook_url:
            return
        import aiohttp
        async with aiohttp.ClientSession() as session:
            payload = {"content": f"🚨 **Erro crítico:**\n```\n{content[:1800]}\n```"}
            await session.post(webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=5))
    except Exception:
        pass


class GlobalErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Instalar handler de exceções não capturadas do Python
        self._install_sys_excepthook()

    def _install_sys_excepthook(self):
        """Captura exceções não tratadas que chegam ao nível do Python."""
        original_hook = sys.excepthook

        def custom_excepthook(exc_type, exc_value, exc_tb):
            if issubclass(exc_type, KeyboardInterrupt):
                original_hook(exc_type, exc_value, exc_tb)
                return
            tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            logger.critical(f"[sys.excepthook] Exceção não capturada:\n{tb}")

        sys.excepthook = custom_excepthook

    @commands.Cog.listener("on_ready")
    async def on_ready_set_asyncio_handler(self):
        """Instala handler de exceções no event loop do bot."""
        _log_asyncio = logging.getLogger("eclipse_store.asyncio")

        def _handler(loop, context):
            exc = context.get("exception")
            if exc is None:
                msg = context.get("message", "?")
                _log_asyncio.error(f"[asyncio] Erro sem exceção: {msg}")
                return
            if isinstance(exc, asyncio.CancelledError):
                return
            tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            _log_asyncio.error(f"[asyncio] Exceção não capturada em task:\n{tb}")

        try:
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(_handler)
        except Exception:
            pass

    @commands.Cog.listener("on_slash_command_error")
    async def on_slash_error(self, inter: disnake.ApplicationCommandInteraction, error: Exception):
        cause = getattr(error, "original", error)
        if _is_silent(cause):
            return
        cmd = getattr(inter.application_command, "name", "?")
        _log_error(f"slash/{cmd} user={inter.user.id}", cause)
        await _try_respond(inter, "Ocorreu um erro inesperado ao executar esse comando. Tente novamente.")

    @commands.Cog.listener("on_interaction_error")
    async def on_interaction_err(self, inter: disnake.Interaction, error: Exception):
        cause = getattr(error, "original", error)
        if _is_silent(cause):
            return
        custom_id = (
            getattr(getattr(inter, "component", None), "custom_id", None)
            or getattr(inter, "custom_id", "?")
        )
        user_id = inter.user.id if inter.user else "?"
        _log_error(f"interaction custom_id={custom_id!r} user={user_id}", cause)
        await _try_respond(inter, "Ocorreu um erro inesperado. Tente novamente em instantes.")

    @commands.Cog.listener("on_error")
    async def on_event_error(self, event: str, *args, **kwargs):
        tb = traceback.format_exc()
        if tb.strip() in ("NoneType: None", "None"):
            return
        logger.error(f"Exceção no listener '{event}':\n{tb}")

    @commands.Cog.listener("on_connect")
    async def on_connect(self):
        logger.info("[Bot] Conectado ao Discord.")

    @commands.Cog.listener("on_disconnect")
    async def on_disconnect(self):
        logger.warning("[Bot] Desconectado do Discord. Aguardando reconexão automática...")

    @commands.Cog.listener("on_resumed")
    async def on_resumed(self):
        logger.info("[Bot] Sessão retomada com sucesso.")


def setup(bot: commands.Bot):
    bot.add_cog(GlobalErrorHandler(bot))
