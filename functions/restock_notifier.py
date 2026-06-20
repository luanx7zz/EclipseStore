"""
Função reutilizável: envia notificação de restock num canal configurado.
Formato visual igual às imagens (NOVO ESTOQUE! com campos e botão Comprar).
"""
import logging
import disnake

logger = logging.getLogger("eclipse_store.restock_notifier")


async def send_restock_notification(bot, product_id: str, campo_id: str, added_count: int, total_count: int, prev_count: int):
    """
    Envia notificação de restock no canal configurado.
    
    Args:
        bot: instância do bot
        product_id: ID do produto
        campo_id: ID do campo de estoque
        added_count: quantidade adicionada agora
        total_count: estoque total atual
        prev_count: estoque anterior (antes de adicionar)
    """
    try:
        from functions.database import database as db
        from functions.emoji import emoji

        prefs = db.get_document("loja_preferences") or {}
        restock_cfg = prefs.get("restock_channel", {})
        
        if not restock_cfg.get("enabled", False):
            return
        
        channel_id = restock_cfg.get("channel_id")
        if not channel_id:
            return
        
        channel = bot.get_channel(int(channel_id))
        if not channel:
            return
        
        # Obter nome do produto e campo
        products = db.get_document("loja_products") or {}
        product = products.get(product_id, {})
        product_name = product.get("name", product_id)
        campos = product.get("campos", {})
        campo = campos.get(campo_id, {})
        campo_name = campo.get("name", campo_id)
        
        # Tipo de menção
        mention_type = restock_cfg.get("mention", "none")
        mention_text = ""
        if mention_type == "everyone":
            mention_text = "@everyone\n"
        elif mention_type == "here":
            mention_text = "@here\n"
        
        # Cor primária
        colors = db.get_document("custom_colors") or {}
        primary_color_hex = colors.get("primary", "#5c5ef0")
        
        # Tentar encontrar link de compra do produto
        product_url = None
        try:
            loja_data = db.get_document("loja_config") or {}
            guild_id = loja_data.get("guild_id")
            if not guild_id:
                for g in bot.guilds:
                    guild_id = g.id
                    break
            # Tentar achar mensagem do produto
            loja_messages = db.get_document("loja_messages") or {}
            msg_data = loja_messages.get(product_id)
            if msg_data and isinstance(msg_data, dict):
                msg_channel_id = msg_data.get("channel_id")
                msg_id = msg_data.get("message_id")
                if msg_channel_id and msg_id and guild_id:
                    product_url = f"https://discord.com/channels/{guild_id}/{msg_channel_id}/{msg_id}"
        except Exception:
            pass
        
        # Timestamp formatado
        import datetime
        now = disnake.utils.utcnow()
        timestamp_discord = f"<t:{int(now.timestamp())}:f>"
        
        mode = db.get_document("custom_mode").get("mode", "embed")
        
        if mode == "components":
            container_kwargs = {}
            if primary_color_hex:
                container_kwargs["accent_colour"] = disnake.Colour(int(primary_color_hex.replace("#", ""), 16))
            
            fields_text = (
                f"{emoji.cardbox} **Estoque atual:** {prev_count}x\n"
                f"➕ **Adicionados:** {added_count}x\n"
                f"{emoji.cardbox} **Estoque total:** {total_count}x\n"
                f"{emoji.clock} **Data:** {timestamp_discord}"
            )
            
            container = disnake.ui.Container(
                disnake.ui.TextDisplay(f"# {emoji.cardbox}  NOVO ESTOQUE!"),
                disnake.ui.Separator(spacing=disnake.SeparatorSpacing.small),
                disnake.ui.TextDisplay(f"**O produto {product_name} foi reestocado na loja!**"),
                disnake.ui.Separator(spacing=disnake.SeparatorSpacing.small),
                disnake.ui.TextDisplay(fields_text),
                **container_kwargs
            )
            
            buttons = []
            if product_url:
                buttons.append(disnake.ui.Button(label="Comprar", emoji="🛒", style=disnake.ButtonStyle.link, url=product_url))
            
            components = [container]
            if buttons:
                components.append(disnake.ui.ActionRow(*buttons))
            
            await channel.send(
                content=mention_text.strip() if mention_text else None,
                components=components,
                flags=disnake.MessageFlags(is_components_v2=True)
            )
        else:
            # Embed mode (como nas imagens de referência)
            embed_color = int(primary_color_hex.replace("#", ""), 16) if primary_color_hex else 0x5c5ef0
            embed = disnake.Embed(
                title=f"📦  NOVO ESTOQUE!",
                description=f"**O produto {product_name} foi reestocado na loja!**",
                color=embed_color,
                timestamp=now
            )
            embed.add_field(name="📦 Estoque atual", value=f"{prev_count}x", inline=True)
            embed.add_field(name="➕ Adicionados", value=f"{added_count}x", inline=True)
            embed.add_field(name="📦 Estoque total", value=f"{total_count}x", inline=True)
            embed.add_field(name="🕐 Data", value=timestamp_discord, inline=False)
            
            # Footer com nome da loja
            loja_data = db.get_document("loja_config") or {}
            loja_nome = loja_data.get("nome", "Loja")
            embed.set_footer(text=loja_nome)
            
            components_list = []
            if product_url:
                view = disnake.ui.View(timeout=None)
                view.add_item(disnake.ui.Button(label="Comprar", emoji="🛒", style=disnake.ButtonStyle.link, url=product_url))
                await channel.send(content=mention_text.strip() if mention_text else None, embed=embed, view=view)
            else:
                await channel.send(content=mention_text.strip() if mention_text else None, embed=embed)
        
        logger.info(f"[Restock] Notificação enviada: produto={product_name} campo={campo_name} total={total_count}")
    except Exception as e:
        logger.error(f"[Restock] Erro ao enviar notificação: {e}")
