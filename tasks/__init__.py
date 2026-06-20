"""Task modules for Eclipse Store Bot."""
from disnake.ext import commands


def setup(bot: commands.Bot):
    # Nubank IMAP 5s monitor
    try:
        from tasks.nubank_imap_task import NubankImapMonitorTask
        bot.add_cog(NubankImapMonitorTask(bot))
    except Exception as e:
        print(f"[Tasks] Nubank IMAP monitor não carregado: {e}")


__all__ = ["setup"]
