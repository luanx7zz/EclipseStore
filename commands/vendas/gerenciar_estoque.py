"""
Comando /gerenciar_estoque — visualiza e gerencia estoque de produtos.
"""
import disnake
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji
from functions.perms import perms
from functions.utils import utils
import logging
logger = logging.getLogger("eclipse_store.commands.gerenciar_estoque")


class GerenciarEstoqueCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def produto_autocomplete(self, inter: disnake.ApplicationCommandInteraction, string: str):
        products = db.get_document("loja_products") or {}
        string = string.lower()
        return [
            disnake.OptionChoice(name=v.get("name", k)[:100], value=k)
            for k, v in products.items()
            if string in v.get("name", "").lower()
        ][:25]

    @commands.slash_command(
        name="gerenciar_estoque",
        description="Visualiza o estoque de um produto",
        guild_ids=[utils.obter_server_principal()],
        default_member_permissions=disnake.Permissions(administrator=True),
    )
    async def gerenciar_estoque(
        self,
        inter: disnake.ApplicationCommandInteraction,
        produto: str = commands.Param(autocomplete=produto_autocomplete, description="Produto"),
    ):
        if not await perms.check(inter.author.id):
            return await inter.response.send_message(
                f"{emoji.wrong} Sem permissão.", ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        products = db.get_document("loja_products") or {}
        p = products.get(produto)
        if not p:
            return await inter.followup.send(
                f"{emoji.wrong} Produto não encontrado.", ephemeral=True
            )
        name = p.get("name", "?")
        campos = p.get("campos", {})
        stock_info = ""
        for cid, cdata in campos.items():
            items = db.get_document(f"loja_stock_{produto}_{cid}") or []
            qty = len(items) if isinstance(items, list) else 0
            stock_info += f"  {emoji.cardbox} **{cdata.get('name', cid)}**: `{qty}` itens\n"
        if not stock_info:
            stock_info = "Sem campos configurados."
        await inter.followup.send(
            f"**{emoji.information} Estoque: {name}**\n{stock_info}",
            ephemeral=True,
        )


def setup(bot: commands.Bot):
    bot.add_cog(GerenciarEstoqueCommand(bot))
