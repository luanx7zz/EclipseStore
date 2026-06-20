"""
Comando /gerenciar_item — gerencia itens individuais no estoque.
"""
import disnake
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji
from functions.perms import perms
from functions.utils import utils
import logging
logger = logging.getLogger("eclipse_store.commands.gerenciar_item")


class GerenciarItemCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="gerenciar_item",
        description="Remove ou visualiza itens específicos do estoque",
        guild_ids=[utils.obter_server_principal()],
        default_member_permissions=disnake.Permissions(administrator=True),
    )
    async def gerenciar_item(
        self,
        inter: disnake.ApplicationCommandInteraction,
        produto_id: str = commands.Param(description="ID do produto"),
        campo_id: str = commands.Param(description="ID do campo", default="default"),
        acao: str = commands.Param(description="Ação", choices=["listar", "limpar"], default="listar"),
    ):
        if not await perms.check(inter.author.id):
            return await inter.response.send_message(
                f"{emoji.wrong} Sem permissão.", ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        stock_key = f"loja_stock_{produto_id}_{campo_id}"
        items = db.get_document(stock_key) or []
        if acao == "listar":
            text = "\n".join(str(i) for i in items[:20]) or "Nenhum item."
            await inter.followup.send(
                f"**{emoji.cardbox} Itens ({len(items)} total):**\n```\n{text}\n```",
                ephemeral=True,
            )
        elif acao == "limpar":
            db.save_document(stock_key, [])
            await inter.followup.send(
                f"{emoji.correct} Estoque de **{produto_id}/{campo_id}** limpo.",
                ephemeral=True,
            )


def setup(bot: commands.Bot):
    bot.add_cog(GerenciarItemCommand(bot))
