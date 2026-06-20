from disnake.ext import commands
from .cog import VipsCog


def setup(bot: commands.Bot):
    bot.add_cog(VipsCog(bot))


__all__ = ["setup"]
