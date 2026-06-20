"""Extensão: facs"""
from disnake.ext import commands
import logging
logger = logging.getLogger("eclipse_store.extensions.facs")

class FacsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

def setup(bot: commands.Bot):
    bot.add_cog(FacsCog(bot))
