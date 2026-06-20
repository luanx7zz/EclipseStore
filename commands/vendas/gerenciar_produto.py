"""
Comando /gerenciar_produto — operações rápidas em produtos (ativar, desativar, duplicar).
"""
import disnake
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji
from functions.perms import perms
from functions.utils import utils
import logging
logger = logging.getLogger("eclipse_store.commands.gerenciar_produto")


class GerenciarProdutoCommand(commands.Cog):
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
        name="gerenciar_produto",
        description="Gerencia um produto (ativar/desativar/duplicar)",
        guild_ids=[utils.obter_server_principal()],
        default_member_permissions=disnake.Permissions(administrator=True),
    )
    async def gerenciar_produto(
        self,
        inter: disnake.ApplicationCommandInteraction,
        produto: str = commands.Param(autocomplete=produto_autocomplete),
        acao: str = commands.Param(choices=["ativar", "desativar", "duplicar"], default="desativar"),
    ):
        if not await perms.check(inter.author.id):
            return await inter.response.send_message(f"{emoji.wrong} Sem permissão.", ephemeral=True)
        await inter.response.defer(ephemeral=True)
        products = db.get_document("loja_products") or {}
        p = products.get(produto)
        if not p:
            return await inter.followup.send(f"{emoji.wrong} Produto não encontrado.", ephemeral=True)
        name = p.get("name", "?")
        if acao == "ativar":
            p["enabled"] = True
        elif acao == "desativar":
            p["enabled"] = False
        elif acao == "duplicar":
            import uuid
            new_id = str(uuid.uuid4())[:8]
            import copy
            products[new_id] = copy.deepcopy(p)
            products[new_id]["name"] = f"{name} (cópia)"
        db.save_document("loja_products", products)
        await inter.followup.send(
            f"{emoji.correct} Produto **{name}**: ação **{acao}** executada.", ephemeral=True
        )


def setup(bot: commands.Bot):
    bot.add_cog(GerenciarProdutoCommand(bot))
