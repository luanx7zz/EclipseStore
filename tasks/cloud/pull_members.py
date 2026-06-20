"""
Tarefa: Puxar membros do SyncCloud.
"""
from disnake.ext import commands
import logging

logger = logging.getLogger("eclipse_store.tasks.cloud.pull_members")


class PullMembersTask(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("[PullMembersTask] Inicializado")


def setup(bot: commands.Bot):
    bot.add_cog(PullMembersTask(bot))
