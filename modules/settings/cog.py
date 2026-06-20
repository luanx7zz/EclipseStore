from disnake.ext import commands
import disnake

from functions.database import database as db
from functions.emoji import emoji
from functions.message import message, embed_message
from functions.plan import should_enable_settings_button

class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def settings_components(self, inter: disnake.MessageInteraction) -> list[disnake.ui.Container]:
        colors = db.get_document("custom_colors")
        primary_color_hex = colors.get("primary")

        container_kwargs = {}
        if primary_color_hex:
            primary_color = int(primary_color_hex.replace("#", ""), 16)
            container_kwargs["accent_colour"] = disnake.Colour(primary_color)

        options = [
            disnake.SelectOption(label="Cargos", value="cargos", emoji=emoji.role, description="Gerencie cargos do servidor"),
            disnake.SelectOption(label="Canais", value="canais", emoji=emoji.textc, description="Gerencie canais do servidor"),
            disnake.SelectOption(label="Formas de Pagamento", value="pagamentos", emoji=emoji.wallet, description="Configure provedores e status"),
            disnake.SelectOption(label="Anti-Fake", value="antifake", emoji=emoji.members, description="Configure proteção contra contas falsas"),
            disnake.SelectOption(label="Gerenciar Permissões", value="permissoes", emoji=emoji.members, description="Adicione ou remova permissões de usuários"),
            disnake.SelectOption(label="Extensões (Em breve)", value="extensoes", emoji=emoji.commands, description="Gerencie as extensões do bot"),
            disnake.SelectOption(label="Notificações", value="notificacoes", emoji=emoji.warn, description="Configure as notificações de vendas"),
            disnake.SelectOption(label="Bloquear Usuários", value="blacklist", emoji=emoji.lock, description="Bloqueie usuários de Comprar em Seu Bot"),
        ]

        return [
            disnake.ui.Container(
                disnake.ui.TextDisplay(f"# {emoji.z0}{emoji.z1}{emoji.z2}{emoji.z3}{emoji.z4}\n-# Painel > **Configurações**"),
                disnake.ui.Separator(),
                disnake.ui.TextDisplay(
                    "Configure e personalize os canais, cargos e formas de pagamento.\n"
                    "Selecione uma seção abaixo para configurar."
                ),
                disnake.ui.Separator(),
                disnake.ui.ActionRow(
                    disnake.ui.StringSelect(
                        custom_id="Configuracoes_Select",
                        placeholder="Selecione uma seção para configurar",
                        options=options,
                    )
                ),
                **container_kwargs,
            ),
            disnake.ui.ActionRow(disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="PainelInicial"))
        ]

    def settings_embed(self, inter: disnake.MessageInteraction):
        colors = db.get_document("custom_colors")
        primary_color_hex = colors.get("primary")

        embed = disnake.Embed(
            title=f"Configurações",
            description="Configure e personalize os canais, cargos e formas de pagamento.\nSelecione uma seção abaixo para configurar.",
            # timestamp=disnake.utils.utcnow()
        )
        if primary_color_hex:
            primary_color = int(primary_color_hex.replace("#", ""), 16)
            embed.color = primary_color

        # embed.set_footer(text=inter.guild.name, icon_url=inter.guild.icon.url if inter.guild.icon else None)
        options = [
            disnake.SelectOption(label="Cargos", value="cargos", emoji=emoji.role, description="Gerencie cargos do servidor"),
            disnake.SelectOption(label="Canais", value="canais", emoji=emoji.textc, description="Gerencie canais do servidor"),
            disnake.SelectOption(label="Formas de Pagamento", value="pagamentos", emoji=emoji.wallet, description="Configure provedores e status"),
            disnake.SelectOption(label="Anti-Fake", value="antifake", emoji=emoji.members, description="Configure proteção contra contas falsas"),
            disnake.SelectOption(label="Gerenciar Permissões", value="permissoes", emoji=emoji.members, description="Adicione ou remova permissões de usuários"),
            disnake.SelectOption(label="Extensões (Em breve)", value="extensoes", emoji=emoji.commands, description="Gerencie as extensões do bot"),
            disnake.SelectOption(label="Notificações", value="notificacoes", emoji=emoji.warn, description="Configure as notificações de vendas"),
            disnake.SelectOption(label="Bloquear Usuários", value="blacklist", emoji=emoji.lock, description="Bloqueie usuários de Comprar em Seu Bot"),
        ]

        components = [
            disnake.ui.ActionRow(
                disnake.ui.StringSelect(
                    custom_id="Configuracoes_Select",
                    placeholder="Selecione uma seção para configurar",
                    options=options,
                )
            ),
            disnake.ui.ActionRow(disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="PainelInicial"))
        ]
        return embed, components

    @commands.Cog.listener("on_button_click")
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "Painel_Configuracoes":
            mode = db.get_document("custom_mode").get("mode")
            if mode == "embed":
                await embed_message.wait(inter, send=False)
                embed, components = self.settings_embed(inter)
                await inter.edit_original_message(content=None, embed=embed, components=components)
            else:
                await message.wait(inter, send=False)
                await inter.edit_original_message(components=self.settings_components(inter))

    @commands.Cog.listener("on_dropdown")
    async def on_dropdown(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "Configuracoes_Select":
            choice = inter.values[0]

            coming_soon = {}
            if choice in coming_soon:
                await inter.response.send_message(
                    "Essa funcionalidade será implementada em breve em próximas atualizações.",
                    ephemeral=True
                )
                return

            if choice == "extensoes":
                await inter.response.send_message(
                    "Essa funcionalidade será implementada em breve em próximas atualizações.",
                    ephemeral=True
                )
                return

            mode = db.get_document("custom_mode").get("mode")
            if choice == "notificacoes":
                from .notificacoes.cog import ConfigureNotifications
                if mode == "embed":
                    await embed_message.wait(inter, send=False)
                    panel = ConfigureNotifications.panel(inter)
                    await inter.edit_original_message(content=None, **panel)
                else:
                    await message.wait(inter, send=False)
                    panel = ConfigureNotifications.panel(inter)
                    await inter.edit_original_message(**panel, flags=disnake.MessageFlags(is_components_v2=True))
            elif choice == "blacklist":
                from .bloquear.cog import ConfigurarBlacklist
                if mode == "embed":
                    await embed_message.wait(inter, send=False)
                    panel = ConfigurarBlacklist.panel(inter)
                    await inter.edit_original_message(content=None, **panel)
                else:
                    await message.wait(inter, send=False)
                    panel = ConfigurarBlacklist.panel(inter)
                    await inter.edit_original_message(**panel, flags=disnake.MessageFlags(is_components_v2=True))
            elif choice == "antifake":
                from .antifake.cog import AntiFakeConfig
                if mode == "embed":
                    await embed_message.wait(inter, send=False)
                    panel = AntiFakeConfig.panel(inter)
                    await inter.edit_original_message(content=None, **panel)
                else:
                    await message.wait(inter, send=False)
                    panel = AntiFakeConfig.panel(inter)
                    await inter.edit_original_message(**panel, flags=disnake.MessageFlags(is_components_v2=True))
            elif choice == "cargos":
                from .cargos.cog import ConfigurarCargos
                if mode == "embed":
                    await embed_message.wait(inter, send=False)
                    embed, components = ConfigurarCargos.cargos_embed(inter)
                    await inter.edit_original_message(content=None, embed=embed, components=components)
                else:
                    await message.wait(inter, send=False)
                    await inter.edit_original_message(components=ConfigurarCargos.cargos_components(inter))
            elif choice == "canais":
                from .canais.cog import ConfigurarCanais
                if mode == "embed":
                    await embed_message.wait(inter, send=False)
                    embed, components = ConfigurarCanais.canais_embed(inter)
                    await inter.edit_original_message(content=None, embed=embed, components=components)
                else:
                    await message.wait(inter, send=False)
                    await inter.edit_original_message(components=ConfigurarCanais.canais_components(inter))
            elif choice == "pagamentos":
                from .payments.cog import ConfigurarPagamentos
                if mode == "embed":
                    await embed_message.wait(inter, send=False)
                    embed, components = ConfigurarPagamentos.pagamentos_embed(inter)
                    await inter.edit_original_message(content=None, embed=embed, components=components)
                else:
                    await message.wait(inter, send=False)
                    await inter.edit_original_message(components=ConfigurarPagamentos.pagamentos_components(inter))
            elif choice == "permissoes":
                from .permissoes.cog import GerenciarPermissoes
                if mode == "embed":
                    await embed_message.wait(inter, send=False)
                    embed, components = GerenciarPermissoes.panel_embed(inter)
                    await inter.edit_original_message(content=None, embed=embed, components=components)
                else:
                    await message.wait(inter, send=False)
                    panel = GerenciarPermissoes.panel(inter)
                    await inter.edit_original_message(**panel, flags=disnake.MessageFlags(is_components_v2=True))