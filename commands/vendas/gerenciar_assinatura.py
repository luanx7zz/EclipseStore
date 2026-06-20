"""
Comando /gerenciar_assinatura — gerencia assinaturas de membros.
"""
import disnake
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji
from functions.perms import perms
from functions.utils import utils
import logging
logger = logging.getLogger("eclipse_store.commands.gerenciar_assinatura")


class GerenciarAssinaturaCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="gerenciar_assinatura",
        description="Gerencia a assinatura de um membro",
        guild_ids=[utils.obter_server_principal()],
        default_member_permissions=disnake.Permissions(administrator=True),
    )
    async def gerenciar_assinatura(
        self,
        inter: disnake.ApplicationCommandInteraction,
        membro: disnake.Member = commands.Param(description="Membro"),
        acao: str = commands.Param(
            description="Ação",
            choices=["cancelar", "renovar", "pausar", "ativar"],
            default="cancelar",
        ),
    ):
        if not await perms.check(inter.author.id):
            return await inter.response.send_message(
                f"{emoji.wrong} Sem permissão.", ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        await inter.followup.send(
            f"{emoji.information} Assinatura de {membro.mention}: ação **{acao}** registrada.",
            ephemeral=True,
        )


def setup(bot: commands.Bot):
    bot.add_cog(GerenciarAssinaturaCommand(bot))
