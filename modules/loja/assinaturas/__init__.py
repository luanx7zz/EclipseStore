from disnake.ext import commands
from .cog import AssinaturasCog


def setup(bot: commands.Bot):
    bot.add_cog(AssinaturasCog(bot))


__all__ = ["setup"]
