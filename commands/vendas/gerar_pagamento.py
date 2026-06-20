"""
Comando /gerar_pagamento — gera link/QR de pagamento manual para um produto.
"""
import disnake
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji
from functions.perms import perms
from functions.utils import utils
import logging
logger = logging.getLogger("eclipse_store.commands.gerar_pagamento")


class GerarPagamentoCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="gerar_pagamento",
        description="Gera um pagamento manual para um membro",
        guild_ids=[utils.obter_server_principal()],
        default_member_permissions=disnake.Permissions(administrator=True),
    )
    async def gerar_pagamento(
        self,
        inter: disnake.ApplicationCommandInteraction,
        membro: disnake.Member = commands.Param(description="Membro que vai pagar"),
        valor: float = commands.Param(description="Valor em R$", ge=0.01),
        descricao: str = commands.Param(description="Descrição do pagamento", default="Pagamento manual"),
    ):
        if not await perms.check(inter.author.id):
            return await inter.response.send_message(
                f"{emoji.wrong} Sem permissão.", ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        await inter.followup.send(
            f"{emoji.information} Pagamento de **R$ {valor:.2f}** para {membro.mention} criado.\n-# Descrição: {descricao}",
            ephemeral=True,
        )


def setup(bot: commands.Bot):
    bot.add_cog(GerarPagamentoCommand(bot))
