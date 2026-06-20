"""
Sistema de Afiliados — Eclipse Store
Cada membro tem um código único. Quando alguém compra com o código,
o afiliado acumula comissão. Admin gerencia saques pelo painel.
"""
import disnake
import secrets
import logging
from datetime import datetime, timezone
from disnake.ext import commands
from typing import Optional

from functions.database import database as db
from functions.emoji import emoji

logger = logging.getLogger("eclipse_store.affiliates")


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def _primary() -> int:
    hex_c = (db.get_document("custom_colors") or {}).get("primary", "#5c5ef0")
    return int(hex_c.replace("#", ""), 16)

def _load_affiliates() -> dict:
    return db.get_document("loja_affiliates") or {"affiliates": {}, "codes": {}}

def _save_affiliates(data: dict):
    db.save_document("loja_affiliates", data)

def _get_or_create_affiliate(user_id: int) -> dict:
    data = _load_affiliates()
    uid = str(user_id)
    if uid not in data["affiliates"]:
        code = secrets.token_urlsafe(5).upper()[:6]
        while code in data.get("codes", {}):
            code = secrets.token_urlsafe(5).upper()[:6]
        affiliate = {
            "user_id": uid,
            "code": code,
            "total_sales": 0,
            "total_commission": 0.0,
            "pending_commission": 0.0,
            "paid_commission": 0.0,
            "sales": [],
            "created_at": _now_ts(),
        }
        data["affiliates"][uid] = affiliate
        data.setdefault("codes", {})[code] = uid
        _save_affiliates(data)
    return data["affiliates"][uid]

def validate_affiliate_code(code: str) -> Optional[str]:
    """Retorna user_id do afiliado se código válido, None caso contrário."""
    data = _load_affiliates()
    return data.get("codes", {}).get(code.upper())

def get_affiliate_discount_percent() -> int:
    """Desconto que o comprador recebe ao usar um código de afiliado."""
    prefs = db.get_document("loja_preferences") or {}
    return prefs.get("affiliate_buyer_discount", 5)

def get_affiliate_commission_percent() -> float:
    """Comissão (%) que o afiliado recebe por cada venda."""
    prefs = db.get_document("loja_preferences") or {}
    return prefs.get("affiliate_commission", 10.0)

def register_affiliate_sale(affiliate_user_id: str, buyer_user_id: str,
                             product_name: str, sale_amount: float, purchase_id: str):
    """Registra uma venda pelo afiliado e adiciona comissão pendente."""
    commission_pct = get_affiliate_commission_percent()
    commission = round(sale_amount * commission_pct / 100, 2)
    data = _load_affiliates()
    affiliate = data["affiliates"].get(affiliate_user_id)
    if not affiliate:
        return
    affiliate["total_sales"] += 1
    affiliate["total_commission"] = round(affiliate.get("total_commission", 0) + commission, 2)
    affiliate["pending_commission"] = round(affiliate.get("pending_commission", 0) + commission, 2)
    affiliate.setdefault("sales", []).append({
        "purchase_id": purchase_id,
        "buyer_id": buyer_user_id,
        "product_name": product_name,
        "amount": sale_amount,
        "commission": commission,
        "ts": _now_ts(),
    })
    data["affiliates"][affiliate_user_id] = affiliate
    _save_affiliates(data)
    logger.info(f"[Affiliate] Comissão R${commission:.2f} para {affiliate_user_id} (venda {purchase_id})")


def _affiliate_status_embed(affiliate: dict, user: disnake.User) -> disnake.Embed:
    code = affiliate.get("code", "?")
    total_sales = affiliate.get("total_sales", 0)
    total_comm = affiliate.get("total_commission", 0.0)
    pending = affiliate.get("pending_commission", 0.0)
    paid = affiliate.get("paid_commission", 0.0)
    discount_pct = get_affiliate_discount_percent()
    comm_pct = get_affiliate_commission_percent()

    embed = disnake.Embed(
        title=f"🔗 Seu Código de Afiliado",
        description=(
            f"**Código:** `{code}`\n"
            f"**Desconto para compradores:** `{discount_pct}%`\n"
            f"**Sua comissão por venda:** `{comm_pct}%`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 **Vendas geradas:** `{total_sales}`\n"
            f"💰 **Comissão total:** `R${total_comm:.2f}`\n"
            f"⏳ **Pendente saque:** `R${pending:.2f}`\n"
            f"✅ **Já pago:** `R${paid:.2f}`"
        ),
        color=_primary(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    embed.set_footer(text="Compartilhe seu código e ganhe comissão em cada venda!")
    return embed


def admin_panel(inter) -> dict:
    data = _load_affiliates()
    affiliates = list(data.get("affiliates", {}).values())
    total_affiliates = len(affiliates)
    total_sales = sum(a.get("total_sales", 0) for a in affiliates)
    total_pending = sum(a.get("pending_commission", 0.0) for a in affiliates)
    total_paid = sum(a.get("paid_commission", 0.0) for a in affiliates)

    top = sorted(affiliates, key=lambda x: x.get("total_commission", 0), reverse=True)[:5]
    top_lines = []
    for i, a in enumerate(top, 1):
        top_lines.append(f"`{i}.` <@{a['user_id']}> — `{a['code']}` — **{a['total_sales']}** venda(s) — R${a['total_commission']:.2f}")

    description = (
        f"**Afiliados ativos:** `{total_affiliates}`\n"
        f"**Total de vendas geradas:** `{total_sales}`\n"
        f"**Comissões pendentes:** `R${total_pending:.2f}`\n"
        f"**Total pago:** `R${total_paid:.2f}`\n\n"
        f"**🏆 Top Afiliados:**\n" + ("\n".join(top_lines) if top_lines else "*Nenhum afiliado ainda.*")
    )

    prefs = db.get_document("loja_preferences") or {}
    discount = prefs.get("affiliate_buyer_discount", 5)
    commission = prefs.get("affiliate_commission", 10.0)

    components = [
        disnake.ui.ActionRow(
            disnake.ui.Button(label="Configurar Comissão", style=disnake.ButtonStyle.blurple,
                              emoji="💰", custom_id="Affiliate_Config"),
            disnake.ui.Button(label="Pagar Afiliado", style=disnake.ButtonStyle.green,
                              emoji="✅", custom_id="Affiliate_Pay"),
            disnake.ui.Button(label="Ver Todos", style=disnake.ButtonStyle.grey,
                              emoji=emoji.members, custom_id="Affiliate_ListAll"),
        ),
        disnake.ui.ActionRow(
            disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey,
                              emoji=emoji.back, custom_id="Painel_Loja")
        )
    ]

    embed = disnake.Embed(title="🔗 Sistema de Afiliados", description=description, color=_primary())
    embed.set_footer(text=f"Comissão: {commission}% | Desconto comprador: {discount}%")
    return {"embed": embed, "components": components}


class AffiliateConfigModal(disnake.ui.Modal):
    def __init__(self):
        prefs = db.get_document("loja_preferences") or {}
        super().__init__(
            title="Configurar Afiliados",
            custom_id="Affiliate_ConfigModal",
            components=[
                disnake.ui.TextInput(label="Comissão do afiliado (%)", custom_id="commission",
                                     style=disnake.TextInputStyle.short,
                                     value=str(prefs.get("affiliate_commission", 10)),
                                     placeholder="Ex: 10", required=True, max_length=4),
                disnake.ui.TextInput(label="Desconto para o comprador (%)", custom_id="buyer_discount",
                                     style=disnake.TextInputStyle.short,
                                     value=str(prefs.get("affiliate_buyer_discount", 5)),
                                     placeholder="Ex: 5", required=True, max_length=3),
            ]
        )

    async def callback(self, inter: disnake.ModalInteraction):
        await inter.response.defer(ephemeral=True)
        try:
            commission = float(inter.resolved_values["commission"].replace(",", "."))
            buyer_discount = int(inter.resolved_values["buyer_discount"])
            if not (0 <= commission <= 50): raise ValueError()
            if not (0 <= buyer_discount <= 50): raise ValueError()
        except ValueError:
            await inter.followup.send("Valores inválidos. Comissão: 0-50%, Desconto: 0-50%.", ephemeral=True)
            return
        prefs = db.get_document("loja_preferences") or {}
        prefs["affiliate_commission"] = commission
        prefs["affiliate_buyer_discount"] = buyer_discount
        db.save_document("loja_preferences", prefs)
        p = admin_panel(inter)
        await inter.edit_original_message(**p)
        await inter.followup.send(f"✅ Comissão: {commission}% | Desconto comprador: {buyer_discount}%", ephemeral=True)


class AffiliatePayModal(disnake.ui.Modal):
    def __init__(self):
        super().__init__(
            title="Pagar Afiliado",
            custom_id="Affiliate_PayModal",
            components=[
                disnake.ui.TextInput(label="ID ou @ do afiliado (user_id)", custom_id="user_id",
                                     style=disnake.TextInputStyle.short, required=True, max_length=20),
            ]
        )

    async def callback(self, inter: disnake.ModalInteraction):
        await inter.response.defer(ephemeral=True)
        raw_uid = inter.resolved_values["user_id"].strip().strip("<@!>")
        try:
            uid = str(int(raw_uid))
        except ValueError:
            await inter.followup.send("ID inválido.", ephemeral=True)
            return
        data = _load_affiliates()
        affiliate = data["affiliates"].get(uid)
        if not affiliate:
            await inter.followup.send("Afiliado não encontrado.", ephemeral=True)
            return
        pending = affiliate.get("pending_commission", 0.0)
        if pending <= 0:
            await inter.followup.send("Afiliado não tem comissão pendente.", ephemeral=True)
            return
        affiliate["paid_commission"] = round(affiliate.get("paid_commission", 0.0) + pending, 2)
        affiliate["pending_commission"] = 0.0
        affiliate["last_paid_at"] = _now_ts()
        data["affiliates"][uid] = affiliate
        _save_affiliates(data)
        # Notificar afiliado
        try:
            user = await inter.client.fetch_user(int(uid))
            await user.send(embed=disnake.Embed(
                title="💰 Pagamento de Comissão Recebido!",
                description=f"Você recebeu **R${pending:.2f}** de comissão de afiliado!\nObrigado por divulgar! 🎉",
                color=0x2ecc71
            ))
        except Exception:
            pass
        p = admin_panel(inter)
        await inter.edit_original_message(**p)
        await inter.followup.send(f"✅ Pagamento de R${pending:.2f} registrado para <@{uid}>!", ephemeral=True)


class AffiliateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="afiliado", description="Gerencie seu código de afiliado.")
    async def afiliado(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        affiliate = _get_or_create_affiliate(inter.user.id)
        embed = _affiliate_status_embed(affiliate, inter.user)
        components = [disnake.ui.ActionRow(
            disnake.ui.Button(label="📋 Copiar Código", style=disnake.ButtonStyle.blurple,
                              custom_id=f"Affiliate_CopyCode:{affiliate['code']}"),
            disnake.ui.Button(label="📊 Minhas Vendas", style=disnake.ButtonStyle.grey,
                              custom_id="Affiliate_MySales"),
        )]
        await inter.followup.send(embed=embed, components=components, ephemeral=True)

    @commands.Cog.listener("on_button_click")
    async def on_affiliate_button(self, inter: disnake.MessageInteraction):
        cid = inter.component.custom_id
        if cid.startswith("Affiliate_CopyCode:"):
            code = cid.split(":", 1)[1]
            await inter.response.send_message(f"Seu código: **`{code}`**\nCompartilhe com amigos e ganhe comissão!", ephemeral=True)

        elif cid == "Affiliate_MySales":
            await inter.response.defer(ephemeral=True)
            data = _load_affiliates()
            affiliate = data["affiliates"].get(str(inter.user.id))
            if not affiliate or not affiliate.get("sales"):
                await inter.followup.send("Você ainda não gerou nenhuma venda.", ephemeral=True)
                return
            sales = sorted(affiliate["sales"], key=lambda x: x.get("ts", 0), reverse=True)[:15]
            lines = []
            for s in sales:
                ts = f"<t:{s['ts']}:d>"
                lines.append(f"• **{s['product_name'][:25]}** — R${s['amount']:.2f} — comissão R${s['commission']:.2f} — {ts}")
            embed = disnake.Embed(title="📊 Suas Vendas como Afiliado", description="\n".join(lines), color=_primary())
            await inter.followup.send(embed=embed, ephemeral=True)

        elif cid == "Affiliate_Config":
            await inter.response.send_modal(AffiliateConfigModal())

        elif cid == "Affiliate_Pay":
            await inter.response.send_modal(AffiliatePayModal())

        elif cid == "Affiliate_ListAll":
            await inter.response.defer(ephemeral=True)
            data = _load_affiliates()
            affiliates = sorted(data.get("affiliates", {}).values(),
                                key=lambda x: x.get("total_commission", 0), reverse=True)[:20]
            lines = [f"`{a['code']}` — <@{a['user_id']}> — {a['total_sales']} venda(s) — R${a['total_commission']:.2f} | pendente: R${a['pending_commission']:.2f}"
                     for a in affiliates]
            embed = disnake.Embed(title="🔗 Todos os Afiliados", description="\n".join(lines) or "*Nenhum*", color=_primary())
            await inter.followup.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(AffiliateCog(bot))
