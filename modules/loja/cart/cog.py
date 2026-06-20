"""
Cart Cog — os handlers principais do carrinho estão em buy_modal.py e checkout.py.
Este arquivo existe para satisfazer imports e pode ser expandido futuramente.
"""
from disnake.ext import commands


class CartCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


def setup(bot: commands.Bot):
    bot.add_cog(CartCog(bot))
