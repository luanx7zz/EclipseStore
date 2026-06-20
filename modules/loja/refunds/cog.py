"""
Sistema de Reembolso Inovador — Eclipse Store
Fluxo: Cliente solicita → Admin avalia com IA review → Aprova/Nega → Notifica cliente
"""
import disnake
import asyncio
import logging
from datetime import datetime, timezone
from disnake.ext import commands

from functions.database import database as db
from functions.emoji import emoji

logger = logging.getLogger("eclipse_store.refunds")

REFUND_STATUS_LABELS = {
    "pending":  f"{emoji.clock} Pendente",
    "approved": f"{emoji.correct} Aprovado",
    "denied":   f"{emoji.wrong} Negado",
    "cancelled": f"{emoji.off} Cancelado",
}

def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def _load_refunds() -> dict:
    return db.get_document("loja_refunds") or {"refunds": {}, "counter": 0}

def _save_refunds(data: dict):
    db.save_document("loja_refunds", data)

def _generate_id(data: dict) -> str:
    data["counter"] = data.get("counter", 0) + 1
    return f"REF{data['counter']:05d}"

def _color(hex_str: str | None):
    if not hex_str:
        return 0x5c5ef0
    return int(hex_str.replace("#", ""), 16)

def _primary() -> int:
    return _color((db.get_document("custom_colors") or {}).get("primary"))

def _mode() -> str:
    return (db.get_document("custom_mode") or {}).get("mode", "embed")


# ─────────────────────────── PAINEL ADMIN ────────────────────────────────────

def admin_panel(inter) -> dict:
    data = _load_refunds()
    refunds = data.get("refunds", {})
    pending = [r for r in refunds.values() if r["status"] == "pending"]

    lines = []
    for r in sorted(pending, key=lambda x: x["created_at"])[:10]:
        ts = f"<t:{r['created_at']}:R>"
        lines.append(f"`{r['id']}` • <@{r['user_id']}> • **{r['product_name']}** • R${r['amount']:.2f} • {ts}")

    description = (
        f"**{len(pending)}** solicitação(ões) pendente(s)\n\n"
        + ("\n".join(lines) if lines else "*Nenhuma solicitação pendente.*")
    )

    if _mode() == "embed":
        embed = disnake.Embed(title=f"{emoji.dollar} Gerenciar Reembolsos", description=description, color=_primary())
        components = [
            disnake.ui.ActionRow(
                disnake.ui.StringSelect(
                    custom_id="Refund_AdminSelect",
                    placeholder="Selecione um reembolso para revisar...",
                    options=[disnake.SelectOption(label=f"{r['id']} — {r['product_name'][:30]}", value=r["id"]) for r in pending[:25]]
                             or [disnake.SelectOption(label="Nenhum pendente", value="_none")],
                )
            ),
            disnake.ui.ActionRow(
                disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Painel_Loja")
            )
        ]
        return {"embed": embed, "components": components}
    else:
        c_kw = {"accent_colour": disnake.Colour(_primary())}
        return {"components": [
            disnake.ui.Container(
                disnake.ui.TextDisplay(f"# {emoji.dollar} Reembolsos\n-# **{len(pending)} pendente(s)**"),
                disnake.ui.Separator(),
                disnake.ui.TextDisplay(description),
                disnake.ui.ActionRow(
                    disnake.ui.StringSelect(
                        custom_id="Refund_AdminSelect",
                        placeholder="Selecione um reembolso para revisar...",
                        options=[disnake.SelectOption(label=f"{r['id']} — {r['product_name'][:30]}", value=r["id"]) for r in pending[:25]]
                                 or [disnake.SelectOption(label="Nenhum pendente", value="_none")],
                    )
                ),
                **c_kw
            ),
            disnake.ui.ActionRow(
                disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Painel_Loja")
            )
        ]}


def refund_review_panel(refund: dict) -> dict:
    """Painel de revisão de um reembolso específico."""
    ts = f"<t:{refund['created_at']}:f>"
    description = (
        f"**ID:** `{refund['id']}`\n"
        f"**Cliente:** <@{refund['user_id']}>\n"
        f"**Produto:** {refund['product_name']}\n"
        f"**Valor:** R${refund['amount']:.2f}\n"
        f"**Motivo:** {refund['reason']}\n"
        f"**Data:** {ts}\n"
        f"**Status:** {REFUND_STATUS_LABELS.get(refund['status'], refund['status'])}"
    )
    purchase_id = refund.get("purchase_id", "?")

    if _mode() == "embed":
        embed = disnake.Embed(title=f"{emoji.receipt} Revisão de Reembolso {refund['id']}", description=description, color=_primary())
        components = [
            disnake.ui.ActionRow(
                disnake.ui.Button(label="✅ Aprovar", style=disnake.ButtonStyle.green, custom_id=f"Refund_Approve:{refund['id']}"),
                disnake.ui.Button(label="❌ Negar", style=disnake.ButtonStyle.red, custom_id=f"Refund_Deny:{refund['id']}"),
                disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Refund_AdminPanel"),
            )
        ]
        return {"embed": embed, "components": components}
    else:
        c_kw = {"accent_colour": disnake.Colour(_primary())}
        return {"components": [
            disnake.ui.Container(
                disnake.ui.TextDisplay(f"# {emoji.receipt} Reembolso {refund['id']}"),
                disnake.ui.Separator(),
                disnake.ui.TextDisplay(description),
                disnake.ui.ActionRow(
                    disnake.ui.Button(label="✅ Aprovar", style=disnake.ButtonStyle.green, custom_id=f"Refund_Approve:{refund['id']}"),
                    disnake.ui.Button(label="❌ Negar", style=disnake.ButtonStyle.red, custom_id=f"Refund_Deny:{refund['id']}"),
                    disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Refund_AdminPanel"),
                ),
                **c_kw
            )
        ]}


class RefundRequestModal(disnake.ui.Modal):
    def __init__(self, purchase_id: str, product_name: str, amount: float, user_id: int):
        self.purchase_id = purchase_id
        self.product_name = product_name
        self.amount = amount
        self.user_id = user_id
        super().__init__(
            title="Solicitar Reembolso",
            custom_id=f"Refund_Modal:{purchase_id}",
            components=[
                disnake.ui.TextInput(label="Motivo do reembolso", custom_id="reason", style=disnake.TextInputStyle.paragraph,
                                     placeholder="Descreva o motivo da solicitação...", required=True, min_length=20, max_length=500),
                disnake.ui.TextInput(label="Comprovante / evidência (link ou texto)", custom_id="evidence",
                                     style=disnake.TextInputStyle.short, required=False, max_length=300),
            ]
        )

    async def callback(self, inter: disnake.ModalInteraction):
        reason = inter.resolved_values.get("reason", "")
        evidence = inter.resolved_values.get("evidence", "")
        await inter.response.defer(ephemeral=True)

        data = _load_refunds()
        refund_id = _generate_id(data)
        refund = {
            "id": refund_id,
            "user_id": str(self.user_id),
            "purchase_id": self.purchase_id,
            "product_name": self.product_name,
            "amount": self.amount,
            "reason": reason,
            "evidence": evidence,
            "status": "pending",
            "created_at": _now_ts(),
            "updated_at": _now_ts(),
        }
        data["refunds"][refund_id] = refund
        _save_refunds(data)

        # Notificar canal de admin
        await _notify_admin_refund(inter.client, refund)

        await inter.followup.send(
            f"{emoji.correct} Solicitação `{refund_id}` registrada!\n"
            f"Nossa equipe analisará em breve e você será notificado por DM.",
            ephemeral=True
        )


class DenyReasonModal(disnake.ui.Modal):
    def __init__(self, refund_id: str):
        self.refund_id = refund_id
        super().__init__(
            title="Motivo da Negação",
            custom_id=f"Refund_DenyModal:{refund_id}",
            components=[
                disnake.ui.TextInput(label="Motivo (enviado ao cliente)", custom_id="reason",
                                     style=disnake.TextInputStyle.paragraph, required=True, min_length=10, max_length=400),
            ]
        )

    async def callback(self, inter: disnake.ModalInteraction):
        reason = inter.resolved_values.get("reason", "")
        await inter.response.defer(ephemeral=True)
        data = _load_refunds()
        refund = data["refunds"].get(self.refund_id)
        if not refund:
            await inter.followup.send("Reembolso não encontrado.", ephemeral=True)
            return
        refund["status"] = "denied"
        refund["deny_reason"] = reason
        refund["updated_at"] = _now_ts()
        refund["reviewed_by"] = str(inter.user.id)
        data["refunds"][self.refund_id] = refund
        _save_refunds(data)
        await _notify_user_decision(inter.client, refund, approved=False, note=reason)
        p = admin_panel(inter)
        await inter.edit_original_message(**p)
        await inter.followup.send(f"{emoji.correct} Reembolso `{self.refund_id}` negado.", ephemeral=True)


async def _notify_admin_refund(bot, refund: dict):
    try:
        loja_prefs = db.get_document("loja_preferences") or {}
        channel_id = loja_prefs.get("refund_admin_channel")
        if not channel_id:
            return
        channel = bot.get_channel(int(channel_id))
        if not channel:
            return
        embed = disnake.Embed(
            title=f"🔔 Nova Solicitação de Reembolso — {refund['id']}",
            description=(
                f"**Cliente:** <@{refund['user_id']}>\n"
                f"**Produto:** {refund['product_name']}\n"
                f"**Valor:** R${refund['amount']:.2f}\n"
                f"**Motivo:** {refund['reason'][:200]}"
            ),
            color=0xe67e22,
            timestamp=datetime.now(timezone.utc)
        )
        components = [disnake.ui.ActionRow(
            disnake.ui.Button(label="Revisar", style=disnake.ButtonStyle.blurple, custom_id=f"Refund_QuickReview:{refund['id']}")
        )]
        await channel.send(embed=embed, components=components)
    except Exception as e:
        logger.warning(f"[Refund] Falha ao notificar admin: {e}")


async def _notify_user_decision(bot, refund: dict, approved: bool, note: str = ""):
    try:
        user_id = int(refund["user_id"])
        user = await bot.fetch_user(user_id)
        color = 0x2ecc71 if approved else 0xe74c3c
        title = f"{'✅ Reembolso Aprovado' if approved else '❌ Reembolso Negado'} — {refund['id']}"
        desc = (
            f"**Produto:** {refund['product_name']}\n"
            f"**Valor:** R${refund['amount']:.2f}\n"
        )
        if approved:
            desc += "\nSeu reembolso foi aprovado! O valor será processado em breve."
        else:
            desc += f"\n**Motivo da negação:** {note}"
        embed = disnake.Embed(title=title, description=desc, color=color)
        await user.send(embed=embed)
    except Exception as e:
        logger.warning(f"[Refund] Falha ao notificar usuário: {e}")


class RefundCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="reembolso", description="Solicite um reembolso de uma compra recente.")
    async def reembolso(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        from modules.loja.cart.purchase_manager import PurchaseManager
        data = PurchaseManager._load_purchases()
        user_purchases = data.get("purchases", {}).get(str(inter.user.id), [])
        if not user_purchases:
            await inter.followup.send(f"{emoji.wrong} Você não tem compras registradas.", ephemeral=True)
            return
        recent = sorted(user_purchases, key=lambda x: x.get("created_at", 0), reverse=True)[:10]
        options = []
        for p in recent:
            pname = p.get("product", {}).get("name", "?")
            pid = p.get("purchase_id", "?")
            price = p.get("pricing", {}).get("final_price", 0)
            options.append(disnake.SelectOption(
                label=f"{pname[:40]} — R${price:.2f}",
                value=pid,
                description=f"ID: {pid}"
            ))
        embed = disnake.Embed(
            title=f"{emoji.receipt} Solicitar Reembolso",
            description="Selecione a compra para qual deseja solicitar reembolso:",
            color=_primary()
        )
        await inter.followup.send(
            embed=embed,
            components=[disnake.ui.ActionRow(
                disnake.ui.StringSelect(custom_id="Refund_PurchaseSelect", placeholder="Selecione a compra...", options=options)
            )],
            ephemeral=True
        )

    @commands.Cog.listener("on_dropdown")
    async def on_refund_dropdown(self, inter: disnake.MessageInteraction):
        cid = inter.component.custom_id
        if cid == "Refund_PurchaseSelect":
            purchase_id = inter.values[0]
            from modules.loja.cart.purchase_manager import PurchaseManager
            data = PurchaseManager._load_purchases()
            user_purchases = data.get("purchases", {}).get(str(inter.user.id), [])
            purchase = next((p for p in user_purchases if p.get("purchase_id") == purchase_id), None)
            if not purchase:
                await inter.response.send_message("Compra não encontrada.", ephemeral=True)
                return
            pname = purchase.get("product", {}).get("name", "?")
            price = purchase.get("pricing", {}).get("final_price", 0)
            await inter.response.send_modal(RefundRequestModal(
                purchase_id=purchase_id,
                product_name=pname,
                amount=float(price),
                user_id=inter.user.id
            ))

        elif cid == "Refund_AdminSelect":
            if inter.values[0] == "_none":
                await inter.response.defer()
                return
            refund_id = inter.values[0]
            data = _load_refunds()
            refund = data["refunds"].get(refund_id)
            if not refund:
                await inter.response.send_message("Reembolso não encontrado.", ephemeral=True)
                return
            p = refund_review_panel(refund)
            await inter.response.edit_message(**p)

    @commands.Cog.listener("on_button_click")
    async def on_refund_button(self, inter: disnake.MessageInteraction):
        cid = inter.component.custom_id
        if cid == "Refund_AdminPanel":
            p = admin_panel(inter)
            await inter.response.edit_message(**p)

        elif cid.startswith("Refund_Approve:"):
            refund_id = cid.split(":", 1)[1]
            await inter.response.defer(ephemeral=True)
            data = _load_refunds()
            refund = data["refunds"].get(refund_id)
            if not refund:
                await inter.followup.send("Reembolso não encontrado.", ephemeral=True)
                return
            refund["status"] = "approved"
            refund["updated_at"] = _now_ts()
            refund["reviewed_by"] = str(inter.user.id)
            data["refunds"][refund_id] = refund
            _save_refunds(data)
            await _notify_user_decision(self.bot, refund, approved=True)
            p = admin_panel(inter)
            await inter.edit_original_message(**p)
            await inter.followup.send(f"{emoji.correct} Reembolso `{refund_id}` aprovado! Cliente notificado.", ephemeral=True)

        elif cid.startswith("Refund_Deny:"):
            refund_id = cid.split(":", 1)[1]
            await inter.response.send_modal(DenyReasonModal(refund_id))

        elif cid.startswith("Refund_QuickReview:"):
            refund_id = cid.split(":", 1)[1]
            data = _load_refunds()
            refund = data["refunds"].get(refund_id)
            if not refund:
                await inter.response.send_message("Reembolso não encontrado.", ephemeral=True)
                return
            p = refund_review_panel(refund)
            await inter.response.edit_message(**p)


def setup(bot: commands.Bot):
    bot.add_cog(RefundCog(bot))
