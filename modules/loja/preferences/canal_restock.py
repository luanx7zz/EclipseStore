"""
Preferência: Canal de Restock
Configura o canal e menção (@everyone/@here/cargo) para notificações de novo estoque.
"""
import disnake
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji
from functions.message import message, embed_message


def _get_prefs() -> dict:
    prefs = db.get_document("loja_preferences") or {}
    return prefs.get("restock_channel", {})


def _save_prefs(data: dict):
    prefs = db.get_document("loja_preferences") or {}
    prefs["restock_channel"] = data
    db.save_document("loja_preferences", prefs)


def panel(inter) -> dict:
    mode = db.get_document("custom_mode").get("mode")
    return _panel_embed(inter) if mode == "embed" else _panel_components(inter)


def _status_text() -> str:
    cfg = _get_prefs()
    enabled = cfg.get("enabled", False)
    channel_id = cfg.get("channel_id")
    mention = cfg.get("mention", "none")

    status = f"{emoji.correct if enabled else emoji.wrong} **Status:** {'`Ativado`' if enabled else '`Desativado`'}\n"
    if channel_id:
        status += f"{emoji.cardbox} **Canal:** <#{channel_id}>\n"
    else:
        status += f"{emoji.cardbox} **Canal:** `Não configurado`\n"

    mention_labels = {"none": "Nenhuma", "everyone": "@everyone", "here": "@here", "role": "Cargo configurado"}
    status += f"{emoji.members} **Menção:** `{mention_labels.get(mention, 'Nenhuma')}`"
    return status


def _panel_components(inter) -> dict:
    colors = db.get_document("custom_colors") or {}
    primary_color_hex = colors.get("primary")
    container_kwargs = {}
    if primary_color_hex:
        container_kwargs["accent_colour"] = disnake.Colour(int(primary_color_hex.replace("#", ""), 16))

    cfg = _get_prefs()
    enabled = cfg.get("enabled", False)

    mention_options = [
        disnake.SelectOption(label="Sem menção", value="none", emoji="🔕", description="Não menciona ninguém"),
        disnake.SelectOption(label="@everyone", value="everyone", emoji="📢", description="Menciona todos do servidor"),
        disnake.SelectOption(label="@here", value="here", emoji="🔔", description="Menciona membros online"),
    ]

    return {"components": [
        disnake.ui.Container(
            disnake.ui.TextDisplay(f"# {emoji.z0}{emoji.z1}{emoji.z2}{emoji.z3}{emoji.z4}\n-# Painel > Loja > **Canal de Restock**"),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay(
                "Quando estoque for adicionado a qualquer produto, o bot envia uma notificação no canal configurado."
                "\n\n" + _status_text()
            ),
            disnake.ui.Separator(),
            disnake.ui.ActionRow(
                disnake.ui.Button(
                    label="Desativar" if enabled else "Ativar",
                    style=disnake.ButtonStyle.red if enabled else disnake.ButtonStyle.green,
                    emoji=emoji.off if enabled else emoji.correct,
                    custom_id="Loja_Restock_Toggle"
                ),
                disnake.ui.Button(
                    label="Definir Canal",
                    style=disnake.ButtonStyle.blurple,
                    emoji=emoji.cardbox,
                    custom_id="Loja_Restock_SetChannel"
                ),
            ),
            disnake.ui.ActionRow(
                disnake.ui.StringSelect(
                    custom_id="Loja_Restock_MencaoSelect",
                    placeholder="Tipo de menção na notificação...",
                    options=mention_options
                )
            ),
            **container_kwargs
        ),
        disnake.ui.ActionRow(
            disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Loja_Preferencias")
        )
    ]}


def _panel_embed(inter) -> dict:
    colors = db.get_document("custom_colors") or {}
    primary_color_hex = colors.get("primary")
    cfg = _get_prefs()
    enabled = cfg.get("enabled", False)

    embed = disnake.Embed(
        title="Canal de Restock",
        description="-# Painel > Loja > **Canal de Restock**\n\n" + _status_text()
    )
    if primary_color_hex:
        embed.color = int(primary_color_hex.replace("#", ""), 16)

    mention_options = [
        disnake.SelectOption(label="Sem menção", value="none", emoji="🔕"),
        disnake.SelectOption(label="@everyone", value="everyone", emoji="📢"),
        disnake.SelectOption(label="@here", value="here", emoji="🔔"),
    ]

    components = [
        disnake.ui.ActionRow(
            disnake.ui.Button(
                label="Desativar" if enabled else "Ativar",
                style=disnake.ButtonStyle.red if enabled else disnake.ButtonStyle.green,
                emoji=emoji.off if enabled else emoji.correct,
                custom_id="Loja_Restock_Toggle"
            ),
            disnake.ui.Button(
                label="Definir Canal",
                style=disnake.ButtonStyle.blurple,
                emoji=emoji.cardbox,
                custom_id="Loja_Restock_SetChannel"
            ),
        ),
        disnake.ui.ActionRow(
            disnake.ui.StringSelect(
                custom_id="Loja_Restock_MencaoSelect",
                placeholder="Tipo de menção na notificação...",
                options=mention_options
            )
        ),
        disnake.ui.ActionRow(
            disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Loja_Preferencias")
        )
    ]
    return {"embed": embed, "components": components}


class RestockChannelPreferences(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_button_click")
    async def on_button(self, inter: disnake.MessageInteraction):
        cid = inter.component.custom_id
        if cid == "Loja_Restock_Toggle":
            mode = db.get_document("custom_mode").get("mode")
            await (embed_message if mode == "embed" else message).wait(inter, send=False)
            cfg = _get_prefs()
            cfg["enabled"] = not cfg.get("enabled", False)
            _save_prefs(cfg)
            p = panel(inter)
            if "embed" in p:
                await inter.edit_original_message(content=None, **p)
            else:
                await inter.edit_original_message(**p)

        elif cid == "Loja_Restock_SetChannel":
            mode = db.get_document("custom_mode").get("mode")
            colors = db.get_document("custom_colors") or {}
            primary_color_hex = colors.get("primary")
            if mode == "components":
                container_kwargs = {}
                if primary_color_hex:
                    container_kwargs["accent_colour"] = disnake.Colour(int(primary_color_hex.replace("#", ""), 16))
                await inter.response.edit_message(
                    components=[
                        disnake.ui.Container(
                            disnake.ui.TextDisplay(f"# {emoji.cardbox}\n-# **Selecionar Canal de Restock**"),
                            disnake.ui.Separator(),
                            disnake.ui.TextDisplay(f"{emoji.information} Selecione o canal onde as notificações de restock serão enviadas:"),
                            disnake.ui.ActionRow(
                                disnake.ui.ChannelSelect(
                                    placeholder="Selecione um canal de texto...",
                                    custom_id="Loja_Restock_ChannelSelect",
                                    channel_types=[disnake.ChannelType.text, disnake.ChannelType.news],
                                    min_values=1,
                                    max_values=1,
                                )
                            ),
                            **container_kwargs
                        ),
                        disnake.ui.ActionRow(
                            disnake.ui.Button(label="Cancelar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Loja_Restock_Back")
                        )
                    ]
                )
            else:
                embed_kwargs = {}
                if primary_color_hex:
                    embed_kwargs["color"] = int(primary_color_hex.replace("#", ""), 16)
                await inter.response.edit_message(
                    embed=disnake.Embed(
                        title="Selecionar Canal de Restock",
                        description=f"{emoji.information} Selecione o canal onde as notificações de restock serão enviadas:",
                        **embed_kwargs
                    ),
                    components=[
                        disnake.ui.ActionRow(
                            disnake.ui.ChannelSelect(
                                placeholder="Selecione um canal de texto...",
                                custom_id="Loja_Restock_ChannelSelect",
                                channel_types=[disnake.ChannelType.text, disnake.ChannelType.news],
                                min_values=1,
                                max_values=1,
                            )
                        ),
                        disnake.ui.ActionRow(
                            disnake.ui.Button(label="Cancelar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Loja_Restock_Back")
                        )
                    ]
                )

        elif cid == "Loja_Restock_Back":
            mode = db.get_document("custom_mode").get("mode")
            await (embed_message if mode == "embed" else message).wait(inter, send=False)
            p = panel(inter)
            if "embed" in p:
                await inter.edit_original_message(content=None, **p)
            else:
                await inter.edit_original_message(**p)

    @commands.Cog.listener("on_dropdown")
    async def on_dropdown(self, inter: disnake.MessageInteraction):
        cid = inter.component.custom_id
        if cid == "Loja_Restock_ChannelSelect":
            mode = db.get_document("custom_mode").get("mode")
            await (embed_message if mode == "embed" else message).wait(inter, send=False)
            channel_id = int(inter.values[0])
            cfg = _get_prefs()
            cfg["channel_id"] = str(channel_id)
            _save_prefs(cfg)
            p = panel(inter)
            if "embed" in p:
                await inter.edit_original_message(content=None, **p)
            else:
                await inter.edit_original_message(**p)

        elif cid == "Loja_Restock_MencaoSelect":
            mode = db.get_document("custom_mode").get("mode")
            await (embed_message if mode == "embed" else message).wait(inter, send=False)
            mention_type = inter.values[0]
            cfg = _get_prefs()
            cfg["mention"] = mention_type
            _save_prefs(cfg)
            p = panel(inter)
            if "embed" in p:
                await inter.edit_original_message(content=None, **p)
            else:
                await inter.edit_original_message(**p)


def setup(bot: commands.Bot):
    bot.add_cog(RestockChannelPreferences(bot))
