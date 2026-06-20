"""
Carrinho Multi-Produto — Eclipse Store
Clientes adicionam múltiplos produtos ao carrinho e compram tudo de uma vez.
"""
import disnake
import asyncio
import logging
from datetime import datetime, timezone
from disnake.ext import commands
from typing import Optional

from functions.database import database as db
from functions.emoji import emoji

logger = logging.getLogger("eclipse_store.multi_cart")

CART_TTL_MINUTES = 30  # carrinho expira em 30 min se não finalizado


def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def _primary() -> int:
    hex_c = (db.get_document("custom_colors") or {}).get("primary", "#5c5ef0")
    return int(hex_c.replace("#", ""), 16)

def _mode() -> str:
    return (db.get_document("custom_mode") or {}).get("mode", "embed")

def _load_multicarts() -> dict:
    return db.get_document("loja_multicarts") or {"carts": {}}

def _save_multicarts(data: dict):
    db.save_document("loja_multicarts", data)

def get_user_cart(user_id: int) -> dict:
    data = _load_multicarts()
    cart = data["carts"].get(str(user_id), {})
    # Expirar carrinho se passou do TTL
    if cart and _now_ts() - cart.get("updated_at", 0) > CART_TTL_MINUTES * 60:
        cart = {}
        data["carts"].pop(str(user_id), None)
        _save_multicarts(data)
    return cart

def save_user_cart(user_id: int, cart: dict):
    data = _load_multicarts()
    cart["updated_at"] = _now_ts()
    data["carts"][str(user_id)] = cart
    _save_multicarts(data)

def clear_user_cart(user_id: int):
    data = _load_multicarts()
    data["carts"].pop(str(user_id), None)
    _save_multicarts(data)

def add_to_cart(user_id: int, product_id: str, campo_id: str,
                product_name: str, campo_name: str, price: float, quantity: int = 1) -> dict:
    cart = get_user_cart(user_id)
    if not cart:
        cart = {"user_id": str(user_id), "items": [], "created_at": _now_ts()}
    items = cart.get("items", [])
    # Verificar se já está no carrinho
    for item in items:
        if item["product_id"] == product_id and item["campo_id"] == campo_id:
            item["quantity"] += quantity
            item["subtotal"] = round(item["price"] * item["quantity"], 2)
            cart["items"] = items
            save_user_cart(user_id, cart)
            return cart
    items.append({
        "product_id": product_id,
        "campo_id": campo_id,
        "product_name": product_name,
        "campo_name": campo_name,
        "price": price,
        "quantity": quantity,
        "subtotal": round(price * quantity, 2),
    })
    cart["items"] = items
    save_user_cart(user_id, cart)
    return cart

def _cart_total(cart: dict) -> float:
    return round(sum(i.get("subtotal", 0) for i in cart.get("items", [])), 2)

def _cart_summary_text(cart: dict) -> str:
    items = cart.get("items", [])
    if not items:
        return "*Carrinho vazio.*"
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(
            f"`{i}.` **{item['product_name']}** — {item['campo_name']}\n"
            f"    {item['quantity']}x R${item['price']:.2f} = **R${item['subtotal']:.2f}**"
        )
    total = _cart_total(cart)
    lines.append(f"\n**Total: R${total:.2f}**")
    return "\n".join(lines)

def cart_panel(user_id: int) -> dict:
    cart = get_user_cart(user_id)
    summary = _cart_summary_text(cart)
    total = _cart_total(cart)
    has_items = bool(cart.get("items"))
    expires_ts = cart.get("updated_at", _now_ts()) + CART_TTL_MINUTES * 60 if has_items else 0

    if _mode() == "embed":
        embed = disnake.Embed(
            title=f"🛒 Seu Carrinho",
            description=summary + (f"\n\n⏳ Expira <t:{expires_ts}:R>" if has_items else ""),
            color=_primary()
        )
        components = [
            disnake.ui.ActionRow(
                disnake.ui.Button(label="✅ Finalizar Compra", style=disnake.ButtonStyle.green,
                                  emoji="🛒", custom_id="MultiCart_Checkout", disabled=not has_items),
                disnake.ui.Button(label="🗑️ Limpar Carrinho", style=disnake.ButtonStyle.red,
                                  custom_id="MultiCart_Clear", disabled=not has_items),
                disnake.ui.Button(label="Remover Item", style=disnake.ButtonStyle.grey,
                                  custom_id="MultiCart_RemoveItem", disabled=not has_items),
            )
        ]
        return {"embed": embed, "components": components}
    else:
        c_kw = {"accent_colour": disnake.Colour(_primary())}
        buttons = [
            disnake.ui.Button(label="✅ Finalizar Compra", style=disnake.ButtonStyle.green,
                              emoji="🛒", custom_id="MultiCart_Checkout", disabled=not has_items),
            disnake.ui.Button(label="🗑️ Limpar", style=disnake.ButtonStyle.red,
                              custom_id="MultiCart_Clear", disabled=not has_items),
        ]
        if has_items:
            buttons.append(disnake.ui.Button(label="Remover Item", style=disnake.ButtonStyle.grey,
                                             custom_id="MultiCart_RemoveItem"))
        return {"components": [
            disnake.ui.Container(
                disnake.ui.TextDisplay(f"# 🛒 Seu Carrinho\n{summary}"
                                       + (f"\n\n⏳ Expira <t:{expires_ts}:R>" if has_items else "")),
                disnake.ui.ActionRow(*buttons),
                **c_kw
            )
        ]}


class MultiCartCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="carrinho", description="Gerencia seu carrinho de compras.")
    async def carrinho(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @carrinho.sub_command(name="ver", description="Ver os itens no seu carrinho.")
    async def carrinho_ver(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        p = cart_panel(inter.user.id)
        await inter.followup.send(**p, ephemeral=True)

    @carrinho.sub_command(name="adicionar", description="Adiciona um produto ao carrinho.")
    async def carrinho_adicionar(
        self,
        inter: disnake.ApplicationCommandInteraction,
        produto: str = commands.Param(description="ID ou nome do produto"),
        campo: str = commands.Param(description="ID ou nome do campo de entrega", default=""),
        quantidade: int = commands.Param(description="Quantidade", default=1, ge=1, le=10),
    ):
        await inter.response.defer(ephemeral=True)
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

        campo_id = None
        campo_obj = None
        if campo:
            for cid, c in campos.items():
                if cid == campo or c.get("name", "").lower() == campo.lower():
                    campo_id = cid
                    campo_obj = c
                    break
        if not campo_id:
            # Se só há um campo, selecionar automaticamente
            if len(campos) == 1:
                campo_id = list(campos.keys())[0]
                campo_obj = list(campos.values())[0]
            else:
                # Mostrar seletor de campo
                options = [disnake.SelectOption(label=c.get("name", cid), value=f"{product_id}:{cid}:{quantidade}")
                           for cid, c in list(campos.items())[:25]]
                await inter.followup.send(
                    f"Selecione o campo para **{product.get('name')}**:",
                    components=[disnake.ui.ActionRow(
                        disnake.ui.StringSelect(custom_id="MultiCart_FieldSelect",
                                                placeholder="Selecione o campo...", options=options)
                    )],
                    ephemeral=True
                )
                return

        price = float(campo_obj.get("price", product.get("price", 0)))
        cart = add_to_cart(
            inter.user.id, product_id, campo_id,
            product.get("name", produto), campo_obj.get("name", campo_id),
            price, quantidade
        )
        total = _cart_total(cart)
        item_count = len(cart.get("items", []))

        await inter.followup.send(
            f"{emoji.correct} **{product.get('name')}** adicionado ao carrinho!\n"
            f"🛒 {item_count} item(s) | Total: **R${total:.2f}**\n\n"
            f"Use `/carrinho ver` para ver ou `/carrinho finalizar` para comprar tudo.",
            ephemeral=True
        )

    @carrinho.sub_command(name="finalizar", description="Finaliza a compra de todos os itens do carrinho.")
    async def carrinho_finalizar(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        cart = get_user_cart(inter.user.id)
        if not cart or not cart.get("items"):
            await inter.followup.send(f"{emoji.wrong} Seu carrinho está vazio.", ephemeral=True)
            return
        await _process_multicart_checkout(inter, cart)

    @carrinho.sub_command(name="limpar", description="Remove todos os itens do carrinho.")
    async def carrinho_limpar(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        clear_user_cart(inter.user.id)
        await inter.followup.send(f"{emoji.correct} Carrinho limpo.", ephemeral=True)

    @commands.Cog.listener("on_button_click")
    async def on_multicart_button(self, inter: disnake.MessageInteraction):
        cid = inter.component.custom_id
        if cid == "MultiCart_Checkout":
            await inter.response.defer(ephemeral=True)
            cart = get_user_cart(inter.user.id)
            if not cart or not cart.get("items"):
                await inter.followup.send(f"{emoji.wrong} Carrinho vazio.", ephemeral=True)
                return
            await _process_multicart_checkout(inter, cart)

        elif cid == "MultiCart_Clear":
            await inter.response.defer(ephemeral=True)
            clear_user_cart(inter.user.id)
            p = cart_panel(inter.user.id)
            await inter.edit_original_message(**p)
            await inter.followup.send(f"{emoji.correct} Carrinho limpo.", ephemeral=True)

        elif cid == "MultiCart_RemoveItem":
            await inter.response.defer(ephemeral=True)
            cart = get_user_cart(inter.user.id)
            items = cart.get("items", [])
            if not items:
                await inter.followup.send("Carrinho já está vazio.", ephemeral=True)
                return
            options = [
                disnake.SelectOption(
                    label=f"{i['product_name']} — {i['campo_name']} ({i['quantity']}x)",
                    value=str(idx)
                )
                for idx, i in enumerate(items[:25])
            ]
            await inter.followup.send(
                "Selecione o item para remover:",
                components=[disnake.ui.ActionRow(
                    disnake.ui.StringSelect(custom_id="MultiCart_RemoveSelect",
                                           placeholder="Remover item...", options=options)
                )],
                ephemeral=True
            )

        elif cid.startswith("MultiCart_AddProduct:"):
            # Botão de adicionar ao carrinho em produtos da loja
            parts = cid.split(":")
            product_id, campo_id = parts[1], parts[2]
            await inter.response.defer(ephemeral=True)
            loja_data = db.get_document("loja_data") or {}
            product = loja_data.get("products", {}).get(product_id, {})
            campos = product.get("campos", {})
            campo_obj = campos.get(campo_id, {})
            price = float(campo_obj.get("price", product.get("price", 0)))
            cart = add_to_cart(
                inter.user.id, product_id, campo_id,
                product.get("name", product_id), campo_obj.get("name", campo_id),
                price, 1
            )
            total = _cart_total(cart)
            await inter.followup.send(
                f"{emoji.correct} Adicionado ao carrinho! **{len(cart.get('items', []))}** item(s) | R${total:.2f}\nUse `/carrinho ver` para revisar.",
                ephemeral=True
            )

    @commands.Cog.listener("on_dropdown")
    async def on_multicart_dropdown(self, inter: disnake.MessageInteraction):
        cid = inter.component.custom_id
        if cid == "MultiCart_RemoveSelect":
            await inter.response.defer(ephemeral=True)
            idx = int(inter.values[0])
            cart = get_user_cart(inter.user.id)
            items = cart.get("items", [])
            if idx < len(items):
                removed = items.pop(idx)
                cart["items"] = items
                save_user_cart(inter.user.id, cart)
                await inter.followup.send(
                    f"{emoji.correct} **{removed['product_name']}** removido do carrinho.",
                    ephemeral=True
                )
            p = cart_panel(inter.user.id)
            await inter.edit_original_message(**p)

        elif cid == "MultiCart_FieldSelect":
            await inter.response.defer(ephemeral=True)
            raw = inter.values[0]
            product_id, campo_id, quantidade = raw.split(":")
            quantidade = int(quantidade)
            loja_data = db.get_document("loja_data") or {}
            product = loja_data.get("products", {}).get(product_id, {})
            campos = product.get("campos", {})
            campo_obj = campos.get(campo_id, {})
            price = float(campo_obj.get("price", product.get("price", 0)))
            cart = add_to_cart(
                inter.user.id, product_id, campo_id,
                product.get("name", product_id), campo_obj.get("name", campo_id),
                price, quantidade
            )
            total = _cart_total(cart)
            await inter.followup.send(
                f"{emoji.correct} **{product.get('name')}** adicionado! {len(cart.get('items', []))} item(s) | R${total:.2f}",
                ephemeral=True
            )

        elif cid == "MultiCart_PaymentSelect":
            await inter.response.defer(ephemeral=True)
            method = inter.values[0]
            cart = get_user_cart(inter.user.id)
            if not cart:
                await inter.followup.send("Carrinho expirou. Adicione os itens novamente.", ephemeral=True)
                return
            await _create_multicart_order(inter, cart, method)


async def _process_multicart_checkout(inter, cart: dict):
    """Mostra seletor de método de pagamento para o carrinho multi-produto."""
    total = _cart_total(cart)
    summary = _cart_summary_text(cart)

    # Obter métodos de pagamento disponíveis
    from modules.loja.cart.buy_modal import get_available_payment_methods
    methods = get_available_payment_methods()

    options = []
    for key, info in list(methods.items())[:25]:
        options.append(disnake.SelectOption(
            label=info.get("label", key),
            value=key,
            emoji=info.get("emoji", "💳"),
        ))

    if not options:
        await inter.followup.send(f"{emoji.wrong} Nenhum método de pagamento configurado.", ephemeral=True)
        return

    if _mode() == "embed":
        embed = disnake.Embed(
            title="🛒 Finalizar Compra",
            description=f"{summary}\n\nSelecione o método de pagamento:",
            color=_primary()
        )
        await inter.followup.send(
            embed=embed,
            components=[disnake.ui.ActionRow(
                disnake.ui.StringSelect(custom_id="MultiCart_PaymentSelect",
                                       placeholder="Método de pagamento...", options=options)
            )],
            ephemeral=True
        )
    else:
        await inter.followup.send(
            components=[disnake.ui.Container(
                disnake.ui.TextDisplay(f"# 🛒 Finalizar Compra\n{summary}\n\n**Selecione o método de pagamento:**"),
                disnake.ui.ActionRow(
                    disnake.ui.StringSelect(custom_id="MultiCart_PaymentSelect",
                                           placeholder="Método de pagamento...", options=options)
                ),
                accent_colour=disnake.Colour(_primary())
            )],
            flags=disnake.MessageFlags(is_components_v2=True),
            ephemeral=True
        )


async def _create_multicart_order(inter, cart: dict, payment_method: str):
    """Cria o pedido do carrinho multi-produto usando o sistema de checkout existente."""
    from modules.loja.cart.checkout import create_checkout
    items = cart.get("items", [])
    if not items:
        await inter.followup.send("Carrinho vazio.", ephemeral=True)
        return

    # Por simplicidade, criar um checkout para o primeiro item
    # e registrar os demais como itens adicionais no mesmo carrinho
    first = items[0]
    try:
        cart_id = await create_checkout(
            bot=inter.client,
            user=inter.user,
            guild=inter.guild,
            product_id=first["product_id"],
            campo_id=first["campo_id"],
            quantity=first["quantity"],
            payment_method=payment_method,
            extra_items=items[1:] if len(items) > 1 else None,
        )
        if cart_id:
            clear_user_cart(inter.user.id)
            await inter.followup.send(
                f"{emoji.correct} Pedido criado! Verifique o thread do carrinho para pagar.",
                ephemeral=True
            )
        else:
            await inter.followup.send(f"{emoji.wrong} Erro ao criar pedido. Tente novamente.", ephemeral=True)
    except Exception as e:
        logger.error(f"[MultiCart] Erro ao criar checkout: {e}")
        await inter.followup.send(f"{emoji.wrong} Erro: {str(e)[:100]}", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(MultiCartCog(bot))
