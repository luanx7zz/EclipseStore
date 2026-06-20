"""
Tarefa: Enviar DMs para usuários verificados no SyncCloud.
"""
from disnake.ext import commands
import logging

logger = logging.getLogger("eclipse_store.tasks.cloud.send_dm")


class SendDMTask(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("[SendDMTask] Inicializado")


def setup(bot: commands.Bot):
    bot.add_cog(SendDMTask(bot))
