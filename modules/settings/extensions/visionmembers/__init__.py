from disnake.ext import commands
from .cog import VisionMembersCog

def setup(bot):
    bot.add_cog(VisionMembersCog(bot))
