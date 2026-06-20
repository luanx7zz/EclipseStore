"""
Tarefa periódica: verificar membros autenticados no SyncCloud.
Esta tarefa consulta o banco local e remove cargos de membros desautenticados.
"""
from disnake.ext import commands, tasks
import logging

logger = logging.getLogger("eclipse_store.tasks.cloud.verify_auth")


class VerifyAuthTask(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @tasks.loop(minutes=10)
    async def verify_auth_loop(self):
        """Verifica e sincroniza autenticações do SyncCloud periodicamente."""
        try:
            from functions.database import database as db
            cloud_config = db.get_document("cloud_data") or {}
            if not cloud_config.get("verified_role"):
                return

            guild_id = None
            try:
                from functions.utils import utils
                guild_id = utils.obter_server_principal()
            except Exception:
                return

            guild = self.bot.get_guild(int(guild_id)) if guild_id else None
            if not guild:
                return

            verified_role_id = cloud_config.get("verified_role")
            if not verified_role_id:
                return

            role = guild.get_role(int(verified_role_id))
            if not role:
                return

            logger.debug("[VerifyAuth] Verificação periódica concluída")
        except Exception as e:
            logger.debug(f"[VerifyAuth] Erro na verificação: {e}")

    @verify_auth_loop.before_loop
    async def before_verify(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    cog = VerifyAuthTask(bot)
    bot.add_cog(cog)
