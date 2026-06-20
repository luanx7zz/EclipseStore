from disnake.ext import commands
import logging

logger = logging.getLogger("eclipse_store.tasks.cloud")


class CloudTasks(commands.Cog):
    """Tarefas periódicas do sistema de Cloud/Sync."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("[CloudTasks] Inicializado")


def setup(bot: commands.Bot):
    bot.add_cog(CloudTasks(bot))
