from disnake.ext import commands
from . import (
    cupom_em_massa,
    entregar,
    perfil,
    ranking,
    sincronizar_clientes,
    gerar_pagamento,
    gerenciar_assinatura,
    gerenciar_estoque,
    gerenciar_item,
    gerenciar_produto,
    produto_vendas,
    rendimentos,
    vip,
    cargo_temporario,
)


def setup(bot: commands.Bot):
    cupom_em_massa.setup(bot)
    entregar.setup(bot)
    perfil.setup(bot)
    ranking.setup(bot)
    sincronizar_clientes.setup(bot)
    gerar_pagamento.setup(bot)
    gerenciar_assinatura.setup(bot)
    gerenciar_estoque.setup(bot)
    gerenciar_item.setup(bot)
    gerenciar_produto.setup(bot)
    produto_vendas.setup(bot)
    rendimentos.setup(bot)
    vip.setup(bot)
    cargo_temporario.setup(bot)
