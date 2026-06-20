"""
Comando /vip — gerencia cargos VIP de membros.
"""
import disnake
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji
from functions.perms import perms
from functions.utils import utils
import logging
logger = logging.getLogger("eclipse_store.commands.vip")


class VipCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="vip",
        description="Gerencia o cargo VIP de um membro",
        guild_ids=[utils.obter_server_principal()],
        default_member_permissions=disnake.Permissions(administrator=True),
    )
    async def vip(
        self,
        inter: disnake.ApplicationCommandInteraction,
        membro: disnake.Member = commands.Param(description="Membro"),
        acao: str = commands.Param(choices=["adicionar", "remover"], default="adicionar"),
    ):
        if not await perms.check(inter.author.id):
            return await inter.response.send_message(f"{emoji.wrong} Sem permissão.", ephemeral=True)
        await inter.response.defer(ephemeral=True)
        cargos = db.get_document("cargos") or {}
        vip_role_id = cargos.get("cargo_vip")
        if not vip_role_id:
            return await inter.followup.send(
                f"{emoji.wrong} Cargo VIP não configurado. Configure em Configurações > Cargos.",
                ephemeral=True,
            )
        role = inter.guild.get_role(int(vip_role_id))
        if not role:
            return await inter.followup.send(f"{emoji.wrong} Cargo VIP não encontrado.", ephemeral=True)
        try:
            if acao == "adicionar":
                await membro.add_roles(role)
                await inter.followup.send(
                    f"{emoji.correct} Cargo VIP adicionado para {membro.mention}.", ephemeral=True
                )
            else:
                await membro.remove_roles(role)
                await inter.followup.send(
                    f"{emoji.correct} Cargo VIP removido de {membro.mention}.", ephemeral=True
                )
        except disnake.Forbidden:
            await inter.followup.send(f"{emoji.wrong} Sem permissão para gerenciar esse cargo.", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(VipCommand(bot))
