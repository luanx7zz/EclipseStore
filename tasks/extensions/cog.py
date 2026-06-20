from disnake.ext import commands
import logging

logger = logging.getLogger("eclipse_store.tasks.extensions")


class ExtensionsTasks(commands.Cog):
    """Tarefas periódicas de extensões (boost, parcerias etc.)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("[ExtensionsTasks] Inicializado")


def setup(bot: commands.Bot):
    bot.add_cog(ExtensionsTasks(bot))
