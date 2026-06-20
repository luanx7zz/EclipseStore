"""
Sistema de Assinaturas — gerencia planos recorrentes.
"""
import disnake
from disnake.ext import commands
import logging

from functions.database import database as db
from functions.emoji import emoji

logger = logging.getLogger("eclipse_store.loja.assinaturas")


class AssinaturasCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("[AssinaturasCog] Inicializado")


def setup(bot: commands.Bot):
    bot.add_cog(AssinaturasCog(bot))
