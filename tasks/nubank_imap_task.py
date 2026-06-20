"""
Task: monitora emails do Nubank a cada 5 segundos.
Quando detecta um PIX confirmado, aprova o carrinho automaticamente.
"""
import asyncio
import logging
from disnake.ext import commands, tasks

from functions.database import database as db
from functions.payments.imap_nubank import monitor_nubank_imap_payments

logger = logging.getLogger("eclipse_store.nubank_monitor")

_processed_carts: set[str] = set()  # evita duplo-processamento


class NubankImapMonitorTask(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._running = False

    @commands.Cog.listener("on_ready")
    async def on_ready_start_monitor(self):
        config = db.get_document("payment_configs") or {}
        nubank_cfg = config.get("nubank_imap", {})
        if not nubank_cfg.get("email") or not nubank_cfg.get("password"):
            logger.info("[NubankIMAP] Credenciais não configuradas — monitor não iniciado.")
            return
        if not self._running:
            self._running = True
            self.nubank_monitor_loop.start()
            logger.info("[NubankIMAP] Monitor iniciado (intervalo: 5s)")

    @tasks.loop(seconds=5)
    async def nubank_monitor_loop(self):
        try:
            approved_list = await monitor_nubank_imap_payments()
        except Exception as e:
            logger.warning(f"[NubankIMAP] Erro ao verificar IMAP: {e}")
            return

        if not approved_list:
            return

        for payment in approved_list:
            cart_id = payment.get("cart_id")
            amount = payment.get("amount", 0)
            payer = payment.get("payer_name", "?")

            if not cart_id:
                continue
            if cart_id in _processed_carts:
                continue

            logger.info(f"[NubankIMAP] PIX confirmado: cart={cart_id} R${amount:.2f} payer={payer!r}")
            _processed_carts.add(cart_id)

            # Chamar aprovação via checkout
            try:
                from modules.loja.cart.checkout import _handle_payment_approved
                await _handle_payment_approved(cart_id, self.bot)
                logger.info(f"[NubankIMAP] Carrinho {cart_id} aprovado com sucesso!")
            except Exception as e:
                logger.error(f"[NubankIMAP] Erro ao aprovar carrinho {cart_id}: {e}")
                _processed_carts.discard(cart_id)

    @nubank_monitor_loop.error
    async def nubank_monitor_error(self, error):
        logger.error(f"[NubankIMAP] Erro na task: {error}")


def setup(bot: commands.Bot):
    bot.add_cog(NubankImapMonitorTask(bot))
