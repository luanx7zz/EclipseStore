from disnake.ext import commands
import logging

logger = logging.getLogger("eclipse_store.tasks.loja")


class LojaTasks(commands.Cog):
    """Tarefas periódicas do sistema de loja (estoque, clientes, cashback)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("[LojaTasks] Inicializado")


def setup(bot: commands.Bot):
    bot.add_cog(LojaTasks(bot))
