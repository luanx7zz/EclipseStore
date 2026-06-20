"""
Comando /cargo_temporario — concede um cargo por tempo determinado.
"""
import disnake
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji
from functions.perms import perms
from functions.utils import utils
import asyncio
import logging
logger = logging.getLogger("eclipse_store.commands.cargo_temporario")


class CargoTemporarioCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="cargo_temporario",
        description="Concede um cargo temporário para um membro",
        guild_ids=[utils.obter_server_principal()],
        default_member_permissions=disnake.Permissions(administrator=True),
    )
    async def cargo_temporario(
        self,
        inter: disnake.ApplicationCommandInteraction,
        membro: disnake.Member = commands.Param(description="Membro"),
        cargo: disnake.Role = commands.Param(description="Cargo"),
        minutos: int = commands.Param(description="Duração em minutos", ge=1, le=43200),
    ):
        if not await perms.check(inter.author.id):
            return await inter.response.send_message(f"{emoji.wrong} Sem permissão.", ephemeral=True)
        await inter.response.defer(ephemeral=True)
        try:
            await membro.add_roles(cargo)
            await inter.followup.send(
                f"{emoji.correct} Cargo {cargo.mention} adicionado para {membro.mention} por **{minutos} minuto(s)**.",
                ephemeral=True,
            )
            await asyncio.sleep(minutos * 60)
            try:
                await membro.remove_roles(cargo)
            except Exception:
                pass
        except disnake.Forbidden:
            await inter.followup.send(f"{emoji.wrong} Sem permissão para gerenciar esse cargo.", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(CargoTemporarioCommand(bot))
