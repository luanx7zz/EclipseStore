"""Extensão: server_fivem"""
from disnake.ext import commands
import logging
logger = logging.getLogger("eclipse_store.extensions.server_fivem")

class ServerFivemCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

def setup(bot: commands.Bot):
    bot.add_cog(ServerFivemCog(bot))
