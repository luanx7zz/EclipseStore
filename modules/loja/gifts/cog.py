"""
Sistema de Gifts — Eclipse Store
Compre um produto e presente outro membro do servidor. 
Após o pagamento, o produto é entregue ao destinatário com uma mensagem personalizada.
"""
import disnake
import asyncio
import logging
from datetime import datetime, timezone
from disnake.ext import commands
from typing import Optional

from functions.database import database as db
from functions.emoji import emoji

logger = logging.getLogger("eclipse_store.gifts")


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def _primary() -> int:
    hex_c = (db.get_document("custom_colors") or {}).get("primary", "#5c5ef0")
    return int(hex_c.replace("#", ""), 16)

def _load_gifts() -> dict:
    return db.get_document("loja_gifts") or {"gifts": {}}

def _save_gifts(data: dict):
    db.save_document("loja_gifts", data)


async def deliver_gift(bot, gift_id: str):
    """Chamado após pagamento aprovado para entregar o gift ao destinatário."""
    data = _load_gifts()
    gift = data["gifts"].get(gift_id)
    if not gift or gift.get("delivered"):
        return

    recipient_id = int(gift["recipient_id"])
    buyer_id = int(gift["buyer_id"])
    product_name = gift["product_name"]
    campo_name = gift.get("campo_name", "")
    note = gift.get("note", "")
    items = gift.get("items", [])

    try:
        recipient = await bot.fetch_user(recipient_id)
        buyer = await bot.fetch_user(buyer_id)

        color = _primary()
        mode = (db.get_document("custom_mode") or {}).get("mode", "embed")

        if mode == "embed":
            embed = disnake.Embed(
                title=f"🎁 Você recebeu um Gift!",
                description=(
                    f"**{buyer.name}** te enviou um presente!\n\n"
                    f"**Produto:** {product_name}\n"
                    + (f"**Campo:** {campo_name}\n" if campo_name else "")
                    + (f"\n💬 *\"{note}\"*" if note else "")
                ),
                color=color,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_thumbnail(url=buyer.display_avatar.url)

            if items:
                items_text = "\n".join(f"`{item}`" for item in items[:20])
                embed.add_field(name="Seus Itens", value=items_text[:1024], inline=False)
                if len(items) > 20:
                    embed.add_field(name="", value=f"*...e mais {len(items) - 20} item(s)*")

            await recipient.send(embed=embed)
        else:
            c_kw = {"accent_colour": disnake.Colour(color)}
            body = (
                f"# 🎁 Você recebeu um Gift!\n"
                f"**{buyer.name}** te enviou um presente!\n\n"
                f"**Produto:** {product_name}\n"
                + (f"**Campo:** {campo_name}\n" if campo_name else "")
                + (f"\n💬 *\"{note}\"*" if note else "")
            )
            items_text = ""
            if items:
                items_text = "\n\n**Seus itens:**\n" + "\n".join(f"`{i}`" for i in items[:20])
            await recipient.send(components=[
                disnake.ui.Container(
                    disnake.ui.TextDisplay(body + items_text),
                    **c_kw
                )
            ], flags=disnake.MessageFlags(is_components_v2=True))

        # Notificar comprador
        try:
            await buyer.send(
                embed=disnake.Embed(
                    title=f"✅ Gift entregue!",
                    description=f"Seu gift de **{product_name}** foi entregue para {recipient.mention}!",
                    color=0x2ecc71
                )
            )
        except Exception:
            pass

        # Marcar como entregue
        gift["delivered"] = True
        gift["delivered_at"] = _now_ts()
        data["gifts"][gift_id] = gift
        _save_gifts(data)
        logger.info(f"[Gift] {gift_id} entregue para {recipient_id} de {buyer_id}")

    except disnake.Forbidden:
        logger.warning(f"[Gift] Destinatário {recipient_id} tem DMs fechadas.")
    except Exception as e:
        logger.error(f"[Gift] Erro ao entregar gift {gift_id}: {e}")


class GiftNoteModal(disnake.ui.Modal):
    """Modal para escrever mensagem de gift."""
    def __init__(self, product_id: str, campo_id: str, recipient_id: int):
        self.product_id = product_id
        self.campo_id = campo_id
        self.recipient_id = recipient_id
        super().__init__(
            title="🎁 Enviar Gift",
            custom_id=f"Gift_Note:{product_id}:{campo_id}:{recipient_id}",
            components=[
                disnake.ui.TextInput(
                    label="Mensagem para o presenteado (opcional)",
                    custom_id="note",
                    style=disnake.TextInputStyle.paragraph,
                    placeholder="Ex: Feliz aniversário! Aproveite 🎉",
                    required=False,
                    max_length=200,
                )
            ]
        )

    async def callback(self, inter: disnake.ModalInteraction):
        await inter.response.defer(ephemeral=True)
        note = inter.resolved_values.get("note", "").strip()

        # Verificar se produto/campo existem e têm estoque
        loja_data = db.get_document("loja_data") or {}
        products = loja_data.get("products", {})
        product = products.get(self.product_id)
        if not product:
            await inter.followup.send(f"{emoji.wrong} Produto não encontrado.", ephemeral=True)
            return

        campos = product.get("campos", {})
        campo = campos.get(self.campo_id)
        if not campo:
            await inter.followup.send(f"{emoji.wrong} Campo não encontrado.", ephemeral=True)
            return

        # Salvar gift pendente — o carrinho será criado normalmente
        # O cart terá uma flag "is_gift" com os dados do gift
        gift_data = {
            "buyer_id": str(inter.user.id),
            "recipient_id": str(self.recipient_id),
            "product_id": self.product_id,
            "product_name": product.get("name", "?"),
            "campo_id": self.campo_id,
            "campo_name": campo.get("name", "?"),
            "note": note,
            "delivered": False,
            "created_at": _now_ts(),
        }

        # Guardar gift temporário com chave por comprador+produto
        pending_key = f"pending_{inter.user.id}_{self.product_id}_{self.campo_id}"
        data = _load_gifts()
        data["gifts"][pending_key] = gift_data
        _save_gifts(data)

        recipient = await inter.client.fetch_user(self.recipient_id)
        await inter.followup.send(
            f"{emoji.correct} Gift configurado para **{recipient.name}**!\n"
            f"Agora prossiga normalmente com o checkout — após o pagamento, o produto será entregue automaticamente.",
            ephemeral=True
        )


class GiftCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="gift", description="Presenteie outro membro com um produto da loja.")
    async def gift(self, inter: disnake.ApplicationCommandInteraction,
                   destinatario: disnake.Member = commands.Param(description="Membro que receberá o gift"),
                   produto: str = commands.Param(description="ID ou nome do produto"),
                   campo: str = commands.Param(description="ID ou nome do campo de entrega", default="")):
        await inter.response.defer(ephemeral=True)

        if destinatario.id == inter.user.id:
            await inter.followup.send(f"{emoji.wrong} Você não pode se presentear.", ephemeral=True)
            return
        if destinatario.bot:
            await inter.followup.send(f"{emoji.wrong} Você não pode presentear um bot.", ephemeral=True)
            return

        loja_data = db.get_document("loja_data") or {}
        products = loja_data.get("products", {})

        product = None
        product_id = None
        for pid, p in products.items():
            if pid == produto or p.get("name", "").lower() == produto.lower():
                product = p
                product_id = pid
                break

        if not product:
            await inter.followup.send(f"{emoji.wrong} Produto `{produto}` não encontrado.", ephemeral=True)
            return

        campos = product.get("campos", {})
        if not campos:
            await inter.followup.send(f"{emoji.wrong} Produto sem campos de entrega.", ephemeral=True)
            return

        # Selecionar campo
        campo_id = None
        campo_obj = None
        if campo:
            for cid, c in campos.items():
                if cid == campo or c.get("name", "").lower() == campo.lower():
                    campo_id = cid
                    campo_obj = c
                    break
        if not campo_id:
            campo_id = list(campos.keys())[0]
            campo_obj = list(campos.values())[0]

        await inter.followup.send(
            f"{emoji.gift} Gift para **{destinatario.display_name}**\n"
            f"**Produto:** {product.get('name')}\n**Campo:** {campo_obj.get('name')}\n\n"
            f"Clique no botão para adicionar uma mensagem e continuar:",
            components=[disnake.ui.ActionRow(
                disnake.ui.Button(
                    label="Escrever mensagem e continuar",
                    style=disnake.ButtonStyle.blurple,
                    emoji="🎁",
                    custom_id=f"Gift_WriteNote:{product_id}:{campo_id}:{destinatario.id}"
                )
            )],
            ephemeral=True
        )

    @commands.Cog.listener("on_button_click")
    async def on_gift_button(self, inter: disnake.MessageInteraction):
        cid = inter.component.custom_id
        if cid.startswith("Gift_WriteNote:"):
            parts = cid.split(":")
            product_id, campo_id, recipient_id = parts[1], parts[2], int(parts[3])
            await inter.response.send_modal(GiftNoteModal(product_id, campo_id, recipient_id))


def setup(bot: commands.Bot):
    bot.add_cog(GiftCog(bot))
