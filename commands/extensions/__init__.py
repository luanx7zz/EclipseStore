from disnake.ext import commands
from . import boost

def setup(bot: commands.Bot):
    boost.setup(bot)

__all__ = ["setup"]
