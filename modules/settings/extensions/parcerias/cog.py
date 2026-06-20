"""Extensão: parcerias"""
from disnake.ext import commands
import logging
logger = logging.getLogger("eclipse_store.extensions.parcerias")

class ParceriasCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

def setup(bot: commands.Bot):
    bot.add_cog(ParceriasCog(bot))
