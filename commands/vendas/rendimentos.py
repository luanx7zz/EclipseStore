"""
Comando /rendimentos — painel de rendimentos e receita da loja.
"""
import disnake
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji
from functions.perms import perms
from functions.utils import utils
import logging
logger = logging.getLogger("eclipse_store.commands.rendimentos")


class RendimentosCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="rendimentos",
        description="Exibe o relatório de rendimentos da loja",
        guild_ids=[utils.obter_server_principal()],
        default_member_permissions=disnake.Permissions(administrator=True),
    )
    async def rendimentos(self, inter: disnake.ApplicationCommandInteraction):
        if not await perms.check(inter.author.id):
            return await inter.response.send_message(f"{emoji.wrong} Sem permissão.", ephemeral=True)
        await inter.response.defer(ephemeral=True)
        try:
            from modules.loja.cart.purchase_manager import PurchaseManager
            stats = PurchaseManager.get_statistics()
        except Exception:
            stats = {}
        total_revenue = stats.get("total_revenue", 0.0)
        total_purchases = stats.get("total_purchases", 0)
        unique_customers = stats.get("unique_customers", 0)
        embed = disnake.Embed(
            title=f"{emoji.money} Rendimentos da Loja",
            color=disnake.Color.gold(),
        )
        embed.add_field(name="💰 Receita Total", value=f"R$ {total_revenue:.2f}", inline=True)
        embed.add_field(name="🛒 Total de Pedidos", value=str(total_purchases), inline=True)
        embed.add_field(name="👥 Clientes Únicos", value=str(unique_customers), inline=True)
        await inter.followup.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(RendimentosCommand(bot))
