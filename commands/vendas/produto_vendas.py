"""
Comando /produto_vendas — exibe relatório de vendas de um produto.
"""
import disnake
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji
from functions.perms import perms
from functions.utils import utils
import logging
logger = logging.getLogger("eclipse_store.commands.produto_vendas")


class ProdutoVendasCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def produto_autocomplete(self, inter, string):
        products = db.get_document("loja_products") or {}
        string = string.lower()
        return [
            disnake.OptionChoice(name=v.get("name", k)[:100], value=k)
            for k, v in products.items()
            if string in v.get("name", "").lower()
        ][:25]

    @commands.slash_command(
        name="produto_vendas",
        description="Relatório de vendas de um produto",
        guild_ids=[utils.obter_server_principal()],
        default_member_permissions=disnake.Permissions(administrator=True),
    )
    async def produto_vendas(
        self,
        inter: disnake.ApplicationCommandInteraction,
        produto: str = commands.Param(autocomplete=produto_autocomplete),
    ):
        if not await perms.check(inter.author.id):
            return await inter.response.send_message(f"{emoji.wrong} Sem permissão.", ephemeral=True)
        await inter.response.defer(ephemeral=True)
        products = db.get_document("loja_products") or {}
        p = products.get(produto)
        if not p:
            return await inter.followup.send(f"{emoji.wrong} Produto não encontrado.", ephemeral=True)
        name = p.get("name", "?")
        try:
            from modules.loja.cart.purchase_manager import PurchaseManager
            stats = PurchaseManager.get_statistics()
        except Exception:
            stats = {}
        prod_stats = stats.get("by_product", {}).get(produto, {})
        count = prod_stats.get("total", 0)
        revenue = prod_stats.get("revenue", 0.0)
        embed = disnake.Embed(
            title=f"{emoji.information} Vendas: {name}",
            description=(
                f"{emoji.cart} **Total vendido:** `{count}`\n{emoji.money} **Receita:** `R$ {revenue:.2f}`"
            ),
            color=disnake.Color.green(),
        )
        await inter.followup.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(ProdutoVendasCommand(bot))
