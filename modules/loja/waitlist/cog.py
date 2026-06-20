"""
Lista de Espera Automática — Eclipse Store
Produto esgotado → cliente clica "Entrar na Fila" → DM automática ao reestocar.
"""
import disnake
import logging
from datetime import datetime, timezone
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji

logger = logging.getLogger("eclipse_store.waitlist")

def _now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

def _primary() -> int:
    hex_c = (db.get_document("custom_colors") or {}).get("primary", "#5c5ef0")
    return int(hex_c.replace("#", ""), 16)

def _load_waitlist() -> dict:
    return db.get_document("loja_waitlist") or {"queues": {}}

def _save_waitlist(data: dict):
    db.save_document("loja_waitlist", data)

def _queue_key(product_id: str, campo_id: str) -> str:
    return f"{product_id}:{campo_id}"

def add_to_waitlist(user_id: int, product_id: str, campo_id: str) -> bool:
    data = _load_waitlist()
    key = _queue_key(product_id, campo_id)
    queue = data.setdefault("queues", {}).setdefault(key, {
        "product_id": product_id, "campo_id": campo_id, "users": []
    })
    uid = str(user_id)
    if any(u["user_id"] == uid for u in queue["users"]):
        return False
    queue["users"].append({"user_id": uid, "added_at": _now_ts(), "notified": False})
    _save_waitlist(data)
    return True

def remove_from_waitlist(user_id: int, product_id: str, campo_id: str):
    data = _load_waitlist()
    key = _queue_key(product_id, campo_id)
    queue = data.get("queues", {}).get(key)
    if queue:
        queue["users"] = [u for u in queue["users"] if u["user_id"] != str(user_id)]
        _save_waitlist(data)

def is_in_waitlist(user_id: int, product_id: str, campo_id: str) -> bool:
    data = _load_waitlist()
    key = _queue_key(product_id, campo_id)
    return any(u["user_id"] == str(user_id) for u in data.get("queues", {}).get(key, {}).get("users", []))

def get_waitlist_count(product_id: str, campo_id: str) -> int:
    data = _load_waitlist()
    key = _queue_key(product_id, campo_id)
    return len(data.get("queues", {}).get(key, {}).get("users", []))

async def notify_waitlist(bot, product_id: str, campo_id: str, product_name: str, campo_name: str):
    """Chamado quando produto é reestocado — notifica todos na fila."""
    data = _load_waitlist()
    key = _queue_key(product_id, campo_id)
    queue = data.get("queues", {}).get(key)
    if not queue or not queue.get("users"):
        return
    color = _primary()
    mode = (db.get_document("custom_mode") or {}).get("mode", "embed")
    notified = []
    for entry in queue["users"]:
        uid = entry["user_id"]
        if entry.get("notified"):
            continue
        try:
            user = await bot.fetch_user(int(uid))
            if mode == "embed":
                embed = disnake.Embed(
                    title="🔔 Produto Disponível!",
                    description=(
                        f"Você estava na lista de espera por **{product_name}** ({campo_name}) "
                        f"e ele foi **reestocado**!\n\nCorra antes que esgote novamente! 🚀"
                    ),
                    color=color, timestamp=datetime.now(timezone.utc)
                )
                await user.send(embed=embed)
            else:
                await user.send(components=[disnake.ui.Container(
                    disnake.ui.TextDisplay(
                        f"# 🔔 Produto Disponível!\n"
                        f"**{product_name}** ({campo_name}) foi reestocado!\nCorra antes que esgote! 🚀"
                    ),
                    accent_colour=disnake.Colour(color)
                )], flags=disnake.MessageFlags(is_components_v2=True))
            entry["notified"] = True
            notified.append(uid)
        except disnake.Forbidden:
            pass
        except Exception as e:
            logger.warning(f"[Waitlist] Erro ao notificar {uid}: {e}")
    queue["users"] = []
    _save_waitlist(data)
    logger.info(f"[Waitlist] {product_id}/{campo_id}: {len(notified)} notificados.")


class WaitlistCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_button_click")
    async def on_waitlist_button(self, inter: disnake.MessageInteraction):
        cid = inter.component.custom_id
        if cid.startswith("Waitlist_Join:"):
            parts = cid.split(":")
            product_id, campo_id = parts[1], parts[2]
            await inter.response.defer(ephemeral=True)
            added = add_to_waitlist(inter.user.id, product_id, campo_id)
            count = get_waitlist_count(product_id, campo_id)
            if added:
                await inter.followup.send(
                    f"{emoji.correct} **Você entrou na lista de espera!**\n"
                    f"Receberá uma DM assim que o produto for reestocado.\n"
                    f"📋 Posição na fila: **#{count}**",
                    ephemeral=True
                )
            else:
                await inter.followup.send(
                    f"{emoji.information} Você já está na lista de espera (#{count}).",
                    components=[disnake.ui.ActionRow(
                        disnake.ui.Button(label="Sair da Fila", style=disnake.ButtonStyle.red,
                                          emoji="🚪", custom_id=f"Waitlist_Leave:{product_id}:{campo_id}")
                    )],
                    ephemeral=True
                )
        elif cid.startswith("Waitlist_Leave:"):
            parts = cid.split(":")
            product_id, campo_id = parts[1], parts[2]
            await inter.response.defer(ephemeral=True)
            remove_from_waitlist(inter.user.id, product_id, campo_id)
            await inter.followup.send(f"{emoji.correct} Você saiu da lista de espera.", ephemeral=True)

    @commands.slash_command(name="filadeespera", description="Veja sua posição nas listas de espera.")
    async def filadeespera(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        data = _load_waitlist()
        uid = str(inter.user.id)
        entries = []
        for key, queue in data.get("queues", {}).items():
            for i, u in enumerate(queue.get("users", []), 1):
                if u["user_id"] == uid and not u.get("notified"):
                    entries.append(f"• **{queue.get('product_id', key)}** — posição **#{i}**")
        if not entries:
            await inter.followup.send(f"{emoji.information} Você não está em nenhuma lista de espera.", ephemeral=True)
            return
        await inter.followup.send(
            embed=disnake.Embed(title="📋 Suas Listas de Espera",
                                description="\n".join(entries), color=_primary()),
            ephemeral=True
        )


def setup(bot: commands.Bot):
    bot.add_cog(WaitlistCog(bot))
