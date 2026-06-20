"""
Sistema de VIPs — painel de gerenciamento no painel da loja.
"""
import disnake
from disnake.ext import commands
import logging

from functions.database import database as db
from functions.emoji import emoji
from functions.message import message, embed_message

logger = logging.getLogger("eclipse_store.loja.vips")


def _get_vip_config() -> dict:
    cargos = db.get_document("cargos") or {}
    prefs = db.get_document("loja_preferences") or {}
    return {
        "cargo_vip_id": cargos.get("cargo_vip"),
        "desconto": prefs.get("vip_desconto", 0),
        "prioridade": prefs.get("vip_prioridade", False),
    }


def _status_text(guild: disnake.Guild | None) -> str:
    cfg = _get_vip_config()
    cargo_id = cfg.get("cargo_vip_id")
    desconto = cfg.get("desconto", 0)
    prioridade = cfg.get("prioridade", False)

    if cargo_id and guild:
        role = guild.get_role(int(cargo_id))
        cargo_txt = role.mention if role else f"`{cargo_id}` (não encontrado)"
        vip_count = len(role.members) if role else 0
    else:
        cargo_txt = "`Não configurado`"
        vip_count = 0

    lines = [
        f"{emoji.shield_star} **Cargo VIP:** {cargo_txt}",
        f"{emoji.members} **VIPs ativos:** `{vip_count}`",
        f"{emoji.dollar} **Desconto VIP:** `{desconto}%`",
        f"{emoji.correct if prioridade else emoji.wrong} **Prioridade de atendimento:** {'`Sim`' if prioridade else '`Não`'}",
    ]
    return "\n".join(lines)


def panel_components(inter) -> dict:
    colors = db.get_document("custom_colors") or {}
    primary_color_hex = colors.get("primary")
    container_kwargs = {}
    if primary_color_hex:
        container_kwargs["accent_colour"] = disnake.Colour(int(primary_color_hex.replace("#", ""), 16))

    cfg = _get_vip_config()
    prioridade = cfg.get("prioridade", False)

    return {"components": [
        disnake.ui.Container(
            disnake.ui.TextDisplay(f"# {emoji.z0}{emoji.z1}{emoji.z2}{emoji.z3}{emoji.z4}\n-# Painel > Loja > **VIPs**"),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay(_status_text(inter.guild if inter.guild else None)),
            disnake.ui.Separator(),
            disnake.ui.ActionRow(
                disnake.ui.Button(label="Configurar Cargo VIP", style=disnake.ButtonStyle.blurple, emoji=emoji.role, custom_id="Loja_Vip_SetRole"),
                disnake.ui.Button(label="Configurar Desconto", style=disnake.ButtonStyle.blurple, emoji=emoji.dollar, custom_id="Loja_Vip_SetDesconto"),
            ),
            disnake.ui.ActionRow(
                disnake.ui.Button(
                    label="Desativar Prioridade" if prioridade else "Ativar Prioridade",
                    style=disnake.ButtonStyle.red if prioridade else disnake.ButtonStyle.green,
                    emoji=emoji.shield_star,
                    custom_id="Loja_Vip_TogglePrioridade"
                ),
                disnake.ui.Button(label="Listar VIPs", style=disnake.ButtonStyle.grey, emoji=emoji.members, custom_id="Loja_Vip_List"),
            ),
            **container_kwargs
        ),
        disnake.ui.ActionRow(
            disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Painel_Loja")
        )
    ]}


def panel_embed(inter) -> dict:
    colors = db.get_document("custom_colors") or {}
    primary_color_hex = colors.get("primary")
    cfg = _get_vip_config()
    prioridade = cfg.get("prioridade", False)

    embed = disnake.Embed(
        title="Sistema VIP",
        description="-# Painel > Loja > **VIPs**\n\n" + _status_text(inter.guild if inter.guild else None)
    )
    if primary_color_hex:
        embed.color = int(primary_color_hex.replace("#", ""), 16)

    components = [
        disnake.ui.ActionRow(
            disnake.ui.Button(label="Configurar Cargo VIP", style=disnake.ButtonStyle.blurple, emoji=emoji.role, custom_id="Loja_Vip_SetRole"),
            disnake.ui.Button(label="Configurar Desconto", style=disnake.ButtonStyle.blurple, emoji=emoji.dollar, custom_id="Loja_Vip_SetDesconto"),
        ),
        disnake.ui.ActionRow(
            disnake.ui.Button(
                label="Desativar Prioridade" if prioridade else "Ativar Prioridade",
                style=disnake.ButtonStyle.red if prioridade else disnake.ButtonStyle.green,
                emoji=emoji.shield_star,
                custom_id="Loja_Vip_TogglePrioridade"
            ),
            disnake.ui.Button(label="Listar VIPs", style=disnake.ButtonStyle.grey, emoji=emoji.members, custom_id="Loja_Vip_List"),
        ),
        disnake.ui.ActionRow(
            disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Painel_Loja")
        )
    ]
    return {"embed": embed, "components": components}


class DescontoVIPModal(disnake.ui.Modal):
    def __init__(self):
        cfg = _get_vip_config()
        super().__init__(
            title="Configurar Desconto VIP",
            components=[
                disnake.ui.TextInput(
                    label="Desconto (%)",
                    custom_id="desconto",
                    style=disnake.TextInputStyle.short,
                    placeholder="Ex: 10 (para 10% de desconto)",
                    value=str(cfg.get("desconto", 0)),
                    required=True,
                    max_length=3,
                )
            ],
            custom_id="Loja_Vip_DescontoModal"
        )

    async def callback(self, inter: disnake.ModalInteraction):
        mode = db.get_document("custom_mode").get("mode")
        await (embed_message if mode == "embed" else message).wait(inter, send=False)
        raw = inter.resolved_values.get("desconto", "0").strip()
        try:
            desconto = int(raw)
            if not 0 <= desconto <= 100:
                raise ValueError()
        except ValueError:
            await inter.followup.send(f"{emoji.wrong} Desconto inválido. Insira um número entre 0 e 100.", ephemeral=True)
            return
        prefs = db.get_document("loja_preferences") or {}
        prefs["vip_desconto"] = desconto
        db.save_document("loja_preferences", prefs)
        p = panel_embed(inter) if mode == "embed" else panel_components(inter)
        if "embed" in p:
            await inter.edit_original_message(content=None, **p)
        else:
            await inter.edit_original_message(**p)


class VipsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.debug("[VipsCog] Inicializado")

    @commands.Cog.listener("on_button_click")
    async def on_button(self, inter: disnake.MessageInteraction):
        cid = inter.component.custom_id
        mode = db.get_document("custom_mode").get("mode")

        if cid == "Loja_Vip_SetRole":
            colors = db.get_document("custom_colors") or {}
            primary_color_hex = colors.get("primary")
            if mode == "components":
                container_kwargs = {}
                if primary_color_hex:
                    container_kwargs["accent_colour"] = disnake.Colour(int(primary_color_hex.replace("#", ""), 16))
                await inter.response.edit_message(components=[
                    disnake.ui.Container(
                        disnake.ui.TextDisplay(f"# {emoji.role}\n-# **Selecionar Cargo VIP**"),
                        disnake.ui.Separator(),
                        disnake.ui.TextDisplay(f"{emoji.information} Selecione o cargo que será atribuído aos VIPs:"),
                        disnake.ui.ActionRow(
                            disnake.ui.RoleSelect(placeholder="Selecione o cargo VIP...", custom_id="Loja_Vip_RoleSelect", min_values=1, max_values=1)
                        ),
                        **container_kwargs
                    ),
                    disnake.ui.ActionRow(
                        disnake.ui.Button(label="Cancelar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Loja_Vip_Back")
                    )
                ])
            else:
                embed_kwargs = {}
                if primary_color_hex:
                    embed_kwargs["color"] = int(primary_color_hex.replace("#", ""), 16)
                await inter.response.edit_message(
                    embed=disnake.Embed(title="Selecionar Cargo VIP", description=f"{emoji.information} Selecione o cargo VIP:", **embed_kwargs),
                    components=[
                        disnake.ui.ActionRow(
                            disnake.ui.RoleSelect(placeholder="Selecione o cargo VIP...", custom_id="Loja_Vip_RoleSelect", min_values=1, max_values=1)
                        ),
                        disnake.ui.ActionRow(
                            disnake.ui.Button(label="Cancelar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="Loja_Vip_Back")
                        )
                    ]
                )

        elif cid == "Loja_Vip_SetDesconto":
            await inter.response.send_modal(DescontoVIPModal())

        elif cid == "Loja_Vip_TogglePrioridade":
            await (embed_message if mode == "embed" else message).wait(inter, send=False)
            prefs = db.get_document("loja_preferences") or {}
            prefs["vip_prioridade"] = not prefs.get("vip_prioridade", False)
            db.save_document("loja_preferences", prefs)
            p = panel_embed(inter) if mode == "embed" else panel_components(inter)
            if "embed" in p:
                await inter.edit_original_message(content=None, **p)
            else:
                await inter.edit_original_message(**p)

        elif cid == "Loja_Vip_List":
            await inter.response.defer(ephemeral=True)
            cfg = _get_vip_config()
            cargo_id = cfg.get("cargo_vip_id")
            if not cargo_id or not inter.guild:
                await inter.followup.send(f"{emoji.wrong} Cargo VIP não configurado.", ephemeral=True)
                return
            role = inter.guild.get_role(int(cargo_id))
            if not role:
                await inter.followup.send(f"{emoji.wrong} Cargo não encontrado.", ephemeral=True)
                return
            members = role.members
            if not members:
                await inter.followup.send(f"{emoji.information} Nenhum membro com o cargo VIP no momento.", ephemeral=True)
                return
            lines = [f"{i+1}. {m.mention} (`{m.id}`)" for i, m in enumerate(members[:30])]
            extra = f"\n*...e mais {len(members) - 30}*" if len(members) > 30 else ""
            await inter.followup.send(
                f"**{emoji.shield_star} VIPs ({len(members)}):**\n" + "\n".join(lines) + extra,
                ephemeral=True
            )

        elif cid == "Loja_Vip_Back":
            await (embed_message if mode == "embed" else message).wait(inter, send=False)
            p = panel_embed(inter) if mode == "embed" else panel_components(inter)
            if "embed" in p:
                await inter.edit_original_message(content=None, **p)
            else:
                await inter.edit_original_message(**p)

    @commands.Cog.listener("on_dropdown")
    async def on_dropdown(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "Loja_Vip_RoleSelect":
            mode = db.get_document("custom_mode").get("mode")
            await (embed_message if mode == "embed" else message).wait(inter, send=False)
            role_id = int(inter.values[0])
            cargos = db.get_document("cargos") or {}
            cargos["cargo_vip"] = str(role_id)
            db.save_document("cargos", cargos)
            p = panel_embed(inter) if mode == "embed" else panel_components(inter)
            if "embed" in p:
                await inter.edit_original_message(content=None, **p)
            else:
                await inter.edit_original_message(**p)


def setup(bot: commands.Bot):
    bot.add_cog(VipsCog(bot))
