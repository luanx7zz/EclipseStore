"""
Personalização de marca — configura nome, slogan, logo e cores da loja.
"""
import disnake
from disnake.ext import commands
import logging
from functions.database import database as db
from functions.emoji import emoji

logger = logging.getLogger("eclipse_store.loja.personalization.marca")


class MarcaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("[MarcaCog] Inicializado")


def setup(bot: commands.Bot):
    bot.add_cog(MarcaCog(bot))
