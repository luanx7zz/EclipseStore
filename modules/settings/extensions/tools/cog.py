"""
Tools extension — funcionalidades administrativas avançadas.
"""
from disnake.ext import commands
import logging
logger = logging.getLogger("eclipse_store.extensions.tools")

class ToolsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

def setup(bot: commands.Bot):
    bot.add_cog(ToolsCog(bot))
