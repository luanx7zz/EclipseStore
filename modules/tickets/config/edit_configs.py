"""
edit_configs.py — Editor de configurações gerais de um painel de tickets.
Expõe views e modais para editar nome, descrição, canal, categoria,
tempo de espera, mensagem de abertura e modo do painel.
"""
import disnake
from disnake.ext import commands
from functions.database import database as db
from functions.emoji import emoji
from functions.message import message, embed_message
import logging

logger = logging.getLogger("eclipse_store.tickets.edit_configs")


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _get_panel(panel_id: str) -> dict | None:
    config = db.get_document("tickets_config") or {}
    return config.get("panels", {}).get(panel_id)


def _save_panel(panel_id: str, panel_data: dict):
    config = db.get_document("tickets_config") or {}
    panels = config.setdefault("panels", {})
    panels[panel_id] = panel_data
    db.save_document("tickets_config", config)


# ─────────────────────────────────────────────
# Modal: Renomear Painel
# ─────────────────────────────────────────────

class RenomearPainelModal(disnake.ui.Modal):
    def __init__(self, panel_id: str):
        self.panel_id = panel_id
        panel = _get_panel(panel_id) or {}
        super().__init__(
            title="Renomear Painel",
            custom_id=f"EditConfigs_Rename_{panel_id}",
            components=[
                disnake.ui.TextInput(
                    label="Novo nome do painel",
                    custom_id="panel_name",
                    max_length=80,
                    value=panel.get("name", ""),
                    placeholder="Ex: Suporte, Vendas, Parcerias...",
                )
            ],
        )

    async def callback(self, inter: disnake.ModalInteraction):
        mode = db.get_document("custom_mode").get("mode", "components")
        if mode == "embed":
            await embed_message.wait(inter, send=False)
        else:
            await message.wait(inter, send=False)

        new_name = inter.text_values["panel_name"].strip()
        if not new_name:
            return await message.error(inter, "O nome não pode ser vazio.")

        config = db.get_document("tickets_config") or {}
        panels = config.get("panels", {})
        if self.panel_id not in panels:
            return await message.error(inter, "Painel não encontrado.")

        panels[self.panel_id]["name"] = new_name
        db.save_document("tickets_config", config)

        await _refresh_edit_panel(inter, self.panel_id, mode)


# ─────────────────────────────────────────────
# Modal: Editar Descrição do Painel
# ─────────────────────────────────────────────

class DescricaoPainelModal(disnake.ui.Modal):
    def __init__(self, panel_id: str):
        self.panel_id = panel_id
        panel = _get_panel(panel_id) or {}
        super().__init__(
            title="Editar Descrição do Painel",
            custom_id=f"EditConfigs_Desc_{panel_id}",
            components=[
                disnake.ui.TextInput(
                    label="Descrição",
                    custom_id="panel_desc",
                    max_length=300,
                    style=disnake.TextInputStyle.paragraph,
                    value=panel.get("description", ""),
                    placeholder="Descreva o propósito deste painel...",
                    required=False,
                )
            ],
        )

    async def callback(self, inter: disnake.ModalInteraction):
        mode = db.get_document("custom_mode").get("mode", "components")
        if mode == "embed":
            await embed_message.wait(inter, send=False)
        else:
            await message.wait(inter, send=False)

        desc = inter.text_values["panel_desc"].strip()
        config = db.get_document("tickets_config") or {}
        panels = config.get("panels", {})
        if self.panel_id not in panels:
            return await message.error(inter, "Painel não encontrado.")

        panels[self.panel_id]["description"] = desc
        db.save_document("tickets_config", config)

        await _refresh_edit_panel(inter, self.panel_id, mode)


# ─────────────────────────────────────────────
# Modal: Tempo Limite de Ticket Inativo
# ─────────────────────────────────────────────

class TempoInativoModal(disnake.ui.Modal):
    def __init__(self, panel_id: str):
        self.panel_id = panel_id
        panel = _get_panel(panel_id) or {}
        inativo = panel.get("preferences", {}).get("close_tickets", {}).get("inactive_time", "")
        super().__init__(
            title="Tempo de Inatividade",
            custom_id=f"EditConfigs_Inativo_{panel_id}",
            components=[
                disnake.ui.TextInput(
                    label="Minutos até fechar ticket inativo (0 = desativado)",
                    custom_id="inactive_time",
                    max_length=6,
                    value=str(inativo) if inativo else "0",
                    placeholder="Ex: 1440 (24 horas)",
                )
            ],
        )

    async def callback(self, inter: disnake.ModalInteraction):
        mode = db.get_document("custom_mode").get("mode", "components")
        if mode == "embed":
            await embed_message.wait(inter, send=False)
        else:
            await message.wait(inter, send=False)

        raw = inter.text_values["inactive_time"].strip()
        try:
            minutes = int(raw)
            if minutes < 0:
                raise ValueError
        except ValueError:
            return await message.error(inter, "Digite um número inteiro positivo (ou 0 para desativar).")

        config = db.get_document("tickets_config") or {}
        panels = config.get("panels", {})
        if self.panel_id not in panels:
            return await message.error(inter, "Painel não encontrado.")

        prefs = panels[self.panel_id].setdefault("preferences", {})
        close_prefs = prefs.setdefault("close_tickets", {})
        close_prefs["inactive_time"] = minutes if minutes > 0 else None
        close_prefs["auto_close_inactive"] = minutes > 0
        db.save_document("tickets_config", config)

        await _refresh_edit_panel(inter, self.panel_id, mode)


# ─────────────────────────────────────────────
# Helper: re-render edit panel view
# ─────────────────────────────────────────────

async def _refresh_edit_panel(inter, panel_id: str, mode: str):
    """Atualiza a mensagem com o painel de configurações."""
    if mode == "components":
        comps = edit_configs_components(inter, panel_id)
        await inter.edit_original_message(content=None, components=comps)
    else:
        embed, comps = edit_configs_embed(inter, panel_id)
        try:
            await inter.edit_original_message(content=None, embed=embed, components=comps)
        except disnake.HTTPException:
            pass


# ─────────────────────────────────────────────
# Components View
# ─────────────────────────────────────────────

def edit_configs_components(inter: disnake.Interaction, panel_id: str) -> list:
    """Retorna os componentes do painel de edição de configurações gerais."""
    config = db.get_document("tickets_config") or {}
    panel = config.get("panels", {}).get(panel_id, {})
    if not panel:
        return []

    primary_color_hex = db.get_document("custom_colors").get("primary")
    container_kwargs = {}
    if primary_color_hex:
        try:
            container_kwargs["accent_colour"] = disnake.Colour(int(primary_color_hex.replace("#", ""), 16))
        except Exception:
            pass

    name = panel.get("name", "Sem nome")
    desc = panel.get("description") or "*(Sem descrição)*"
    enabled = panel.get("enabled", False)
    mode = panel.get("mode", "channel")
    prefs = panel.get("preferences", {})
    close_prefs = prefs.get("close_tickets", {})
    inactive_time = close_prefs.get("inactive_time")
    inactive_txt = f"`{inactive_time} min`" if inactive_time else "`Desativado`"

    status_emoji = emoji.on if enabled else emoji.off
    mode_emoji = "💬" if mode == "channel" else "📂"
    mode_txt = "Canal" if mode == "channel" else "Tópico"

    info_text = (
        f"{status_emoji} **Status:** `{'Ativado' if enabled else 'Desativado'}`\n"
        f"{mode_emoji} **Modo:** `{mode_txt}`\n"
        f"{emoji.message} **Nome:** `{name}`\n"
        f"{emoji.information} **Descrição:** {desc}\n"
        f"⏱️ **Fechar inativo:** {inactive_txt}"
    )

    container = disnake.ui.Container(
        disnake.ui.TextDisplay(
            f"# {emoji.z0}{emoji.z1}{emoji.z2}{emoji.z3}{emoji.z4}\n"
            f"-# Gerenciar Tickets > Editar Painel > **{name}** > **Configurações**"
        ),
        disnake.ui.Separator(),
        disnake.ui.TextDisplay(info_text),
        disnake.ui.Separator(spacing=disnake.SeparatorSpacing.small),
        disnake.ui.ActionRow(
            disnake.ui.Button(
                label="Renomear",
                style=disnake.ButtonStyle.primary,
                emoji="✏️",
                custom_id=f"EditConfigs_Rename_{panel_id}",
            ),
            disnake.ui.Button(
                label="Descrição",
                style=disnake.ButtonStyle.secondary,
                emoji="📝",
                custom_id=f"EditConfigs_Desc_{panel_id}",
            ),
            disnake.ui.Button(
                label="Tempo Inativo",
                style=disnake.ButtonStyle.secondary,
                emoji="⏱️",
                custom_id=f"EditConfigs_Inativo_{panel_id}",
            ),
        ),
        **container_kwargs,
    )

    back_row = disnake.ui.ActionRow(
        disnake.ui.Button(
            label="Voltar",
            style=disnake.ButtonStyle.grey,
            emoji=emoji.back,
            custom_id=f"TicketEdit_BackToPanel_{panel_id}",
        )
    )

    return [container, back_row]


# ─────────────────────────────────────────────
# Embed View
# ─────────────────────────────────────────────

class EditConfigsViewEmbed(disnake.ui.View):
    def __init__(self, panel_id: str):
        super().__init__(timeout=None)
        self.add_item(
            disnake.ui.Button(
                label="Renomear",
                style=disnake.ButtonStyle.primary,
                emoji="✏️",
                custom_id=f"EditConfigs_Rename_{panel_id}",
            )
        )
        self.add_item(
            disnake.ui.Button(
                label="Descrição",
                style=disnake.ButtonStyle.secondary,
                emoji="📝",
                custom_id=f"EditConfigs_Desc_{panel_id}",
            )
        )
        self.add_item(
            disnake.ui.Button(
                label="Tempo Inativo",
                style=disnake.ButtonStyle.secondary,
                emoji="⏱️",
                custom_id=f"EditConfigs_Inativo_{panel_id}",
            )
        )
        self.add_item(
            disnake.ui.Button(
                label="Voltar",
                style=disnake.ButtonStyle.grey,
                emoji=emoji.back,
                custom_id=f"TicketEdit_BackToPanel_{panel_id}",
                row=1,
            )
        )


def edit_configs_embed(inter: disnake.Interaction, panel_id: str):
    config = db.get_document("tickets_config") or {}
    panel = config.get("panels", {}).get(panel_id, {})
    if not panel:
        return None, None

    name = panel.get("name", "Sem nome")
    desc = panel.get("description") or "*(Sem descrição)*"
    enabled = panel.get("enabled", False)
    mode_val = panel.get("mode", "channel")
    mode_txt = "Canal" if mode_val == "channel" else "Tópico"
    prefs = panel.get("preferences", {})
    close_prefs = prefs.get("close_tickets", {})
    inactive_time = close_prefs.get("inactive_time")
    inactive_txt = f"{inactive_time} min" if inactive_time else "Desativado"

    primary_color_hex = db.get_document("custom_colors").get("primary")
    color = int(primary_color_hex.replace("#", ""), 16) if primary_color_hex else 0x5865F2

    embed = disnake.Embed(
        title=f"⚙️ Configurações: {name}",
        color=color,
    )
    embed.add_field(name="Status", value="✅ Ativado" if enabled else "❌ Desativado", inline=True)
    embed.add_field(name="Modo", value=mode_txt, inline=True)
    embed.add_field(name="Descrição", value=desc, inline=False)
    embed.add_field(name="Fechar Inativo", value=inactive_txt, inline=True)

    return embed, EditConfigsViewEmbed(panel_id)


# ─────────────────────────────────────────────
# Listener helper (usado no cog principal)
# ─────────────────────────────────────────────

async def handle_edit_configs_button(inter: disnake.MessageInteraction, custom_id: str):
    """
    Processa botões com prefixo 'EditConfigs_'.
    Chamado do listener principal em tickets/config/cog.py.
    """
    parts = custom_id.split("_", 2)
    if len(parts) < 3:
        return
    action = parts[1]
    panel_id = parts[2]

    if action == "Rename":
        await inter.response.send_modal(RenomearPainelModal(panel_id))
    elif action == "Desc":
        await inter.response.send_modal(DescricaoPainelModal(panel_id))
    elif action == "Inativo":
        await inter.response.send_modal(TempoInativoModal(panel_id))
