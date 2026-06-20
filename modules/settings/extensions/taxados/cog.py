"""Extensão: taxados"""
from disnake.ext import commands
import logging
logger = logging.getLogger("eclipse_store.extensions.taxados")

class TaxadosCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

def setup(bot: commands.Bot):
    bot.add_cog(TaxadosCog(bot))
