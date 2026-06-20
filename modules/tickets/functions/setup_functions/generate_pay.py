import disnake
from functions.database import database as db
from functions.emoji import emoji


async def generate_pay(inter: disnake.MessageInteraction):
    await inter.response.defer(ephemeral=True)

    tickets_data = db.get_document("tickets_data") or {}

    ticket_info = None
    user_id_found = None
    for panel_id, users in tickets_data.get("panels", {}).items():
        for user_id, tickets_list in users.items():
            for ticket in tickets_list:
                if ticket.get("ticket_id") == inter.channel.id:
                    ticket_info = ticket
                    user_id_found = user_id
                    break
            if ticket_info:
                break
        if ticket_info:
            break

    if not ticket_info:
        await inter.followup.send(
            f"{emoji.wrong} Não foi possível encontrar os dados deste ticket.",
            ephemeral=True
        )
        return

    cart_id = ticket_info.get("cart_id") or ticket_info.get("thread_id")

    if not cart_id:
        await inter.followup.send(
            f"{emoji.information} Este ticket não possui um carrinho vinculado.\n"
            f"Para gerar um pagamento, crie um produto na loja e adicione ao carrinho do cliente.",
            ephemeral=True
        )
        return

    cart_data = db.get_document(f"carts_{cart_id}") or db.get_document("carts") or {}

    if isinstance(cart_data, dict) and str(cart_id) in cart_data:
        cart_data = cart_data[str(cart_id)]

    payment_methods = db.get_document("payments_config") or {}
    active_methods = []
    for method, config in payment_methods.items():
        if isinstance(config, dict) and config.get("enabled"):
            active_methods.append(method.upper())

    methods_text = ", ".join(active_methods) if active_methods else "Nenhum método configurado"

    await inter.followup.send(
        f"{emoji.information} **Informações de Pagamento do Ticket**\n\n"
        f"{emoji.cart if hasattr(emoji, 'cart') else '🛒'} **Carrinho ID:** `{cart_id}`\n"
        f"{emoji.money if hasattr(emoji, 'money') else '💳'} **Métodos disponíveis:** {methods_text}\n\n"
        f"Para processar o pagamento, vá até o carrinho do cliente e use o botão **Checkout**.\n"
        f"O link do carrinho: <#{cart_id}>" if cart_id else "",
        ephemeral=True
    )
