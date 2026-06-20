"""
Flash Sale Automática — Eclipse Store
Admin cria venda relâmpago com desconto, duração e anúncio automático.
Task verifica expiração a cada 30s e encerra automaticamente.
"""
import disnake
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from disnake.ext import commands, tasks
from typing import Optional

from functions.database import database as db
from functions.emoji import emoji

logger = logging.getLogger("eclipse_store.flash_sale")


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def _primary() -> int:
    hex_c = (db.get_document("custom_colors") or {}).get("primary", "#e74c3c")
    return int(hex_c.replace("#", ""), 16)

def _mode() -> str:
    return (db.get_document("custom_mode") or {}).get("mode", "embed")

def _load_sales() -> dict:
    return db.get_document("loja_flash_sales") or {"sales": {}}

def _save_sales(data: dict):
    db.save_document("loja_flash_sales", data)

def get_active_flash_sale(product_id: str) -> Optional[dict]:
    """Retorna flash sale ativa para um produto, ou None."""
    data = _load_sales()
    now = _now_ts()
    for sale in data.get("sales", {}).values():
        if sale.get("product_id") == product_id and sale.get("active") and sale.get("ends_at", 0) > now:
            return sale
    return None

def apply_flash_sale_price(product_id: str, original_price: float) -> tuple[float, Optional[dict]]:
    """Retorna (preço_final, sale_data) — se não houver sale, retorna preço original."""
    sale = get_active_flash_sale(product_id)
    if not sale:
        return original_price, None
    discount = sale.get("discount_percent", 0)
    final = round(original_price * (1 - discount / 100), 2)
    return final, sale


class FlashSaleCreateModal(disnake.ui.Modal):
    def __init__(self, product_id: str, product_name: str):
        self.product_id = product_id
        self.product_name = product_name
        super().__init__(
            title="Criar Flash Sale",
            custom_id=f"FlashSale_Create:{product_id}",
            components=[
                disnake.ui.TextInput(label="Desconto (%)", custom_id="discount",
                                     style=disnake.TextInputStyle.short,
                                     placeholder="Ex: 30 (para 30% de desconto)", required=True, max_length=3),
                disnake.ui.TextInput(label="Duração (minutos)", custom_id="duration",
                                     style=disnake.TextInputStyle.short,
                                     placeholder="Ex: 60 (1 hora)", required=True, max_length=4),
                disnake.ui.TextInput(label="Mensagem de anúncio (opcional)", custom_id="message",
                                     style=disnake.TextInputStyle.paragraph,
                                     placeholder="Descrição da promoção...", required=False, max_length=300),
            ]
        )

    async def callback(self, inter: disnake.ModalInteraction):
        await inter.response.defer(ephemeral=True)
        try:
            discount = int(inter.resolved_values["discount"].strip())
            duration = int(inter.resolved_values["duration"].strip())
            if not (1 <= discount <= 99):
                raise ValueError("discount")
            if not (1 <= duration <= 10080):
                raise ValueError("duration")
        except ValueError:
            await inter.followup.send(f"{emoji.wrong} Valores inválidos. Desconto: 1-99%, Duração: 1-10080 min.", ephemeral=True)
            return

        message = inter.resolved_values.get("message", "").strip()
        now = _now_ts()
        ends_at = now + duration * 60
        sale_id = f"SALE{now}"

        data = _load_sales()
        # Desativar venda anterior deste produto
        for s in data["sales"].values():
            if s.get("product_id") == self.product_id and s.get("active"):
                s["active"] = False

        sale = {
            "id": sale_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "discount_percent": discount,
            "duration_min": duration,
            "starts_at": now,
            "ends_at": ends_at,
            "active": True,
            "message": message,
            "created_by": str(inter.user.id),
        }
        data["sales"][sale_id] = sale
        _save_sales(data)

        # Anunciar no canal de restock (reutilizamos o canal configurado)
        asyncio.create_task(_announce_flash_sale(inter.client, sale, started=True))

        ends_discord = f"<t:{ends_at}:R>"
        await inter.followup.send(
            f"{emoji.correct} Flash Sale criada!\n"
            f"**{self.product_name}** com **{discount}%** de desconto por **{duration} min** (encerra {ends_discord})",
            ephemeral=True
        )


async def _announce_flash_sale(bot, sale: dict, started: bool = True):
    """Anuncia início ou fim de flash sale no canal configurado."""
    try:
        prefs = db.get_document("loja_preferences") or {}
        restock_cfg = prefs.get("restock_channel", {})
        channel_id = restock_cfg.get("channel_id")
        if not channel_id:
            return
        channel = bot.get_channel(int(channel_id))
        if not channel:
            return

        mention_type = restock_cfg.get("mention", "none")
        content = "@everyone\n" if mention_type == "everyone" else ("@here\n" if mention_type == "here" else None)

        ends_ts = sale.get("ends_at", 0)
        discount = sale.get("discount_percent", 0)
        pname = sale.get("product_name", "Produto")

        if started:
            embed = disnake.Embed(
                title="⚡ FLASH SALE!",
                description=(
                    f"**{pname}** está com **{discount}% OFF** por tempo limitado!\n\n"
                    + (f"📢 {sale['message']}\n\n" if sale.get("message") else "")
                    + f"⏰ Encerra <t:{ends_ts}:R> (<t:{ends_ts}:t>)"
                ),
                color=0xe74c3c,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text="Flash Sale — corre antes que acabe!")
        else:
            embed = disnake.Embed(
                title="⏰ Flash Sale Encerrada",
                description=f"A promoção de **{discount}% OFF** no produto **{pname}** foi encerrada.",
                color=0x95a5a6,
                timestamp=datetime.now(timezone.utc)
            )

        await channel.send(content=content, embed=embed)
    except Exception as e:
        logger.warning(f"[FlashSale] Erro ao anunciar: {e}")


class FlashSaleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_ready")
    async def start_flash_sale_task(self):
        if not self.check_expired_sales.is_running():
            self.check_expired_sales.start()

    @tasks.loop(seconds=30)
    async def check_expired_sales(self):
        """Encerra flash sales expiradas automaticamente."""
        data = _load_sales()
        now = _now_ts()
        changed = False
        for sale in data["sales"].values():
            if sale.get("active") and sale.get("ends_at", 0) <= now:
                sale["active"] = False
                changed = True
                asyncio.create_task(_announce_flash_sale(self.bot, sale, started=False))
                logger.info(f"[FlashSale] Venda {sale['id']} encerrada automaticamente.")
        if changed:
            _save_sales(data)

    @commands.slash_command(name="flashsale", description="Gerencia Flash Sales da loja.")
    async def flashsale(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @flashsale.sub_command(name="criar", description="Cria uma Flash Sale para um produto.")
    async def flashsale_criar(
        self,
        inter: disnake.ApplicationCommandInteraction,
        produto: str = commands.Param(description="ID ou nome do produto"),
        desconto: int = commands.Param(description="Desconto em % (ex: 30)", ge=1, le=99),
        duracao: int = commands.Param(description="Duração em minutos (ex: 60)", ge=1, le=10080),
        anuncio: str = commands.Param(description="Mensagem de anúncio", default=""),
    ):
        from functions.perms import perms
        if not await perms.check(inter.user.id):
            await inter.response.send_message("Sem permissão.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True)

        # Buscar produto
        products = (db.get_document("loja_data") or {}).get("products", {})
        product = None
        for pid, p in products.items():
            if pid == produto or p.get("name", "").lower() == produto.lower():
                product = p
                product["_id"] = pid
                break

        if not product:
            await inter.followup.send(f"{emoji.wrong} Produto `{produto}` não encontrado.", ephemeral=True)
            return

        now = _now_ts()
        ends_at = now + duracao * 60
        sale_id = f"SALE{now}"

        data = _load_sales()
        for s in data["sales"].values():
            if s.get("product_id") == product["_id"] and s.get("active"):
                s["active"] = False

        sale = {
            "id": sale_id,
            "product_id": product["_id"],
            "product_name": product.get("name", produto),
            "discount_percent": desconto,
            "duration_min": duracao,
            "starts_at": now,
            "ends_at": ends_at,
            "active": True,
            "message": anuncio,
            "created_by": str(inter.user.id),
        }
        data["sales"][sale_id] = sale
        _save_sales(data)

        asyncio.create_task(_announce_flash_sale(inter.client, sale, started=True))

        ends_discord = f"<t:{ends_at}:R>"
        await inter.followup.send(
            f"{emoji.correct} Flash Sale criada! **{product.get('name')}** com **{desconto}% OFF** encerra {ends_discord}",
            ephemeral=True
        )

    @flashsale.sub_command(name="encerrar", description="Encerra uma Flash Sale ativa.")
    async def flashsale_encerrar(
        self,
        inter: disnake.ApplicationCommandInteraction,
        produto: str = commands.Param(description="ID ou nome do produto"),
    ):
        from functions.perms import perms
        if not await perms.check(inter.user.id):
            await inter.response.send_message("Sem permissão.", ephemeral=True)
            return
        await inter.response.defer(ephemeral=True)
        data = _load_sales()
        found = False
        for sale in data["sales"].values():
            if sale.get("active") and (sale.get("product_id") == produto or sale.get("product_name", "").lower() == produto.lower()):
                sale["active"] = False
                found = True
                asyncio.create_task(_announce_flash_sale(self.bot, sale, started=False))
        if found:
            _save_sales(data)
            await inter.followup.send(f"{emoji.correct} Flash Sale encerrada.", ephemeral=True)
        else:
            await inter.followup.send(f"{emoji.wrong} Nenhuma flash sale ativa encontrada.", ephemeral=True)

    @flashsale.sub_command(name="listar", description="Lista todas as Flash Sales ativas.")
    async def flashsale_listar(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        data = _load_sales()
        now = _now_ts()
        active = [s for s in data["sales"].values() if s.get("active") and s.get("ends_at", 0) > now]
        if not active:
            await inter.followup.send("Nenhuma Flash Sale ativa no momento.", ephemeral=True)
            return
        lines = []
        for s in active:
            ends = f"<t:{s['ends_at']}:R>"
            lines.append(f"• **{s['product_name']}** — **{s['discount_percent']}% OFF** (encerra {ends})")
        embed = disnake.Embed(title="⚡ Flash Sales Ativas", description="\n".join(lines), color=0xe74c3c)
        await inter.followup.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(FlashSaleCog(bot))
