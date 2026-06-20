import disnake
from disnake.ext import commands

from datetime import datetime
from functions.emoji import emoji
from functions.database import database as db
from functions.perms import perms
from functions.message import message, embed_message
from functions.utils import utils
from functions.plan import should_enable_panel_button

class PainelCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_salutation(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "bom dia! ☀️"
        elif 12 <= hour < 18:
            return "boa tarde! 🌞"
        else:
            return "boa noite! 🌙"

    def PainelComponents(self, inter: disnake.MessageInteraction, primary_color_hex: str = None, button_states: dict = None) -> list[disnake.ui.Container]:
        container_kwargs = {}
        if primary_color_hex:
            primary_color = int(primary_color_hex.replace("#", ""), 16)
            container_kwargs["accent_colour"] = disnake.Colour(primary_color)

        # Usar estados pré-calculados dos botões se fornecidos
        if button_states is None:
            button_states = {
                "loja": should_enable_panel_button("loja"),
                "ticket": should_enable_panel_button("ticket"),
                "cloud": should_enable_panel_button("cloud"),
                "personalizacao": should_enable_panel_button("personalizacao"),
                "automacoes": should_enable_panel_button("automacoes"),
                "protection": should_enable_panel_button("protection"),
                "sorteios": should_enable_panel_button("sorteios"),
                "configuracoes": should_enable_panel_button("configuracoes"),
            }

        return [
            disnake.ui.Container(
                disnake.ui.TextDisplay(f"# {emoji.z0}{emoji.z1}{emoji.z2}{emoji.z3}{emoji.z4}\nOlá senhor(a) **{inter.user.name}**, {self._get_salutation()} \n-# Aqui você pode **configurar** e **personalizar** as funcionalidades do seu **Zenity Pro**."),
                disnake.ui.Separator(spacing=disnake.SeparatorSpacing.small),
                disnake.ui.ActionRow(
                    disnake.ui.Button(label="Configurar Loja", style=disnake.ButtonStyle.grey, emoji=emoji.cart, custom_id="Painel_Loja", disabled=not button_states["loja"]),
                    disnake.ui.Button(label="Gerenciar Ticket", style=disnake.ButtonStyle.grey, emoji=emoji.ticket, custom_id="Painel_Ticket", disabled=not button_states["ticket"]),
                    disnake.ui.Button(label="ZProCloud", style=disnake.ButtonStyle.grey, emoji=emoji.cloud, custom_id="Painel_Cloud", disabled=not button_states["cloud"]),
                ),
                disnake.ui.ActionRow(
                    disnake.ui.Button(label="Ver Rendimento", style=disnake.ButtonStyle.grey, emoji=emoji.chart, custom_id="Painel_Rendimentos", disabled=not button_states["ticket"]),
                    disnake.ui.Button(label="Personalização", style=disnake.ButtonStyle.grey, emoji=emoji.wand, custom_id="Painel_Personalizacao", disabled=not button_states["personalizacao"]),
                    disnake.ui.Button(label="Automações", style=disnake.ButtonStyle.grey, emoji=emoji.reload, custom_id="Painel_Automacoes", disabled=not button_states["automacoes"]),
                ),
                disnake.ui.ActionRow(
                    disnake.ui.Button(label="Proteção do Servidor", style=disnake.ButtonStyle.grey, emoji=emoji.shield, custom_id="Painel_Protection", disabled=not button_states["protection"]),
                    disnake.ui.Button(label="Sorteios", style=disnake.ButtonStyle.grey, emoji=emoji.giveaway, custom_id="Painel_Sorteios", disabled=not button_states["sorteios"]),
                    disnake.ui.Button(label="Configurações", style=disnake.ButtonStyle.grey, emoji=emoji.config, custom_id="Painel_Configuracoes", disabled=not button_states["configuracoes"]),
                ),
                **container_kwargs,
            ),
            disnake.ui.ActionRow(
                disnake.ui.Button(label="Eclipse Store", style=disnake.ButtonStyle.grey, disabled=True),
            )
        ]

    def PainelEmbed(self, inter: disnake.MessageInteraction, primary_color_hex: str = None, button_states: dict = None):
        embed = disnake.Embed(
            title=f"Painel",
            description=f"Olá senhor(a) **{inter.user.name}**, {self._get_salutation()} \n-# Aqui você pode **configurar** e **personalizar** as funcionalidades do seu **Zenity Pro**.",
        )
        if primary_color_hex:
            primary_color = int(primary_color_hex.replace("#", ""), 16)
            embed.color = primary_color
        
        # Usar estados pré-calculados dos botões se fornecidos
        if button_states is None:
            button_states = {
                "loja": should_enable_panel_button("loja"),
                "ticket": should_enable_panel_button("ticket"),
                "cloud": should_enable_panel_button("cloud"),
                "personalizacao": should_enable_panel_button("personalizacao"),
                "automacoes": should_enable_panel_button("automacoes"),
                "protection": should_enable_panel_button("protection"),
                "sorteios": should_enable_panel_button("sorteios"),
                "configuracoes": should_enable_panel_button("configuracoes"),
            }
        
        # embed.set_footer(text=inter.guild.name, icon_url=inter.guild.icon.url if inter.guild.icon else None)
        components = [
            disnake.ui.ActionRow(
                disnake.ui.Button(label="Configurar Loja", style=disnake.ButtonStyle.grey, emoji=emoji.cart, custom_id="Painel_Loja", disabled=not button_states["loja"]),
                disnake.ui.Button(label="Gerenciar Ticket", style=disnake.ButtonStyle.grey, emoji=emoji.ticket, custom_id="Painel_Ticket", disabled=not button_states["ticket"]),
                disnake.ui.Button(label="ZProCloud", style=disnake.ButtonStyle.grey, emoji=emoji.cloud, custom_id="Painel_Cloud", disabled=not button_states["cloud"]),
            ),
            disnake.ui.ActionRow(
                disnake.ui.Button(label="Ver Rendimento", style=disnake.ButtonStyle.grey, emoji=emoji.chart, custom_id="Painel_Rendimentos", disabled=not button_states["ticket"]),
                disnake.ui.Button(label="Personalização", style=disnake.ButtonStyle.grey, emoji=emoji.wand, custom_id="Painel_Personalizacao", disabled=not button_states["personalizacao"]),
                disnake.ui.Button(label="Automações", style=disnake.ButtonStyle.grey, emoji=emoji.reload, custom_id="Painel_Automacoes", disabled=not button_states["automacoes"]),
            ),
            disnake.ui.ActionRow(
                disnake.ui.Button(label="Proteção do Servidor", style=disnake.ButtonStyle.grey, emoji=emoji.shield, custom_id="Painel_Protection", disabled=not button_states["protection"]),
                disnake.ui.Button(label="Sorteios", style=disnake.ButtonStyle.grey, emoji=emoji.giveaway, custom_id="Painel_Sorteios", disabled=not button_states["sorteios"]),
                disnake.ui.Button(label="Configurações", style=disnake.ButtonStyle.grey, emoji=emoji.config, custom_id="Painel_Configuracoes", disabled=not button_states["configuracoes"]),
            )
        ]
        return embed, components

    @commands.slash_command(
        name="painel",
        description="Abre o painel de controle do bot.",
        guild_ids=[utils.obter_server_principal()],
    )
    async def painel(self, inter: disnake.ApplicationCommandInteraction):
        # Buscar dados do banco uma única vez
        mode_data = db.get_document("custom_mode")
        mode = mode_data.get("mode") if mode_data else "components"
        
        colors = db.get_document("custom_colors")
        primary_color_hex = colors.get("primary") if colors else None

        if mode == "embed":
            await embed_message.wait(inter, send=True)
        else:
            await message.wait(inter, send=True)

        if not await perms.check(inter.user.id):
            if mode == "embed":
                await embed_message.error(inter, "Você não tem permissão para usar este comando", send=False)
            else:
                await message.error(inter, "Você não tem permissão para usar este comando", send=False)
            return

        # Pré-calcular estados dos botões uma única vez
        button_states = {
            "loja": should_enable_panel_button("loja"),
            "ticket": should_enable_panel_button("ticket"),
            "cloud": should_enable_panel_button("cloud"),
            "personalizacao": should_enable_panel_button("personalizacao"),
            "automacoes": should_enable_panel_button("automacoes"),
            "protection": should_enable_panel_button("protection"),
            "sorteios": should_enable_panel_button("sorteios"),
            "configuracoes": should_enable_panel_button("configuracoes"),
        }

        if mode == "embed":
            embed, components = self.PainelEmbed(inter, primary_color_hex, button_states)
            await inter.edit_original_response(content=None, embed=embed, components=components)
        else:
            await inter.edit_original_response(
                components=self.PainelComponents(inter, primary_color_hex, button_states),
            )

    @commands.Cog.listener("on_button_click")
    async def Painel_Button_Listener(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith("Painel"):
            return

        if inter.component.custom_id == "PainelInicial":
            # Buscar dados do banco uma única vez
            mode_data = db.get_document("custom_mode")
            mode = mode_data.get("mode") if mode_data else "components"
            
            colors = db.get_document("custom_colors")
            primary_color_hex = colors.get("primary") if colors else None

            if mode == "embed":
                await embed_message.wait(inter)
            else:
                await message.wait(inter)

            # Pré-calcular estados dos botões uma única vez
            button_states = {
                "loja": should_enable_panel_button("loja"),
                "ticket": should_enable_panel_button("ticket"),
                "cloud": should_enable_panel_button("cloud"),
                "personalizacao": should_enable_panel_button("personalizacao"),
                "automacoes": should_enable_panel_button("automacoes"),
                "protection": should_enable_panel_button("protection"),
                "sorteios": should_enable_panel_button("sorteios"),
                "configuracoes": should_enable_panel_button("configuracoes"),
            }

            if mode == "embed":
                embed, components = self.PainelEmbed(inter, primary_color_hex, button_states)
                await inter.edit_original_message(content=None, embed=embed, components=components)
            else:
                await inter.edit_original_message(
                    components=self.PainelComponents(inter, primary_color_hex, button_states),
                )
        elif inter.component.custom_id == "Painel_Protection":
            # Verificar se é owner
            config = db.obter("config.json")
            owner_id = config.get("bot", {}).get("owner")
            
            if str(inter.user.id) != str(owner_id):
                await inter.response.send_message(
                    f"{emoji.wrong} Apenas o dono do bot pode acessar esta funcionalidade.",
                    ephemeral=True
                )
                return
            
            protection_cog = self.bot.get_cog("ProtectionCog")
            if protection_cog:
                await protection_cog.display_protection_panel(inter)
        elif inter.component.custom_id == "Painel_Automacoes":
            automations_cog = self.bot.get_cog("AutomationModulesCog")
            if automations_cog:
                await automations_cog.display_automations_panel(inter)
        elif inter.component.custom_id == "Painel_Ticket":
            ticket_cog = self.bot.get_cog("TicketConfigCog")
            if ticket_cog:
                await ticket_cog.display_ticket_panel(inter)
        elif inter.component.custom_id == "Painel_Sorteios":
            giveaways_cog = self.bot.get_cog("Giveaways")
            if giveaways_cog:
                await giveaways_cog.display_giveaways_panel(inter)
        elif inter.component.custom_id == "Painel_Cloud":
            cloud_cog = self.bot.get_cog("Cloud")
            if cloud_cog:
                await cloud_cog.display_cloud_panel(inter)
        elif inter.component.custom_id == "Painel_Rendimentos":
            rendimentos_cog = self.bot.get_cog("RendimentosSystem")
            if rendimentos_cog:
                # Buscar dados do banco uma única vez
                mode_data = db.get_document("custom_mode")
                mode = mode_data.get("mode") if mode_data else "components"
                
                if mode == "embed":
                    await embed_message.wait(inter)
                else:
                    await message.wait(inter)
                
                panel_data = rendimentos_cog.panel(inter)
                if mode == "embed":
                    embed, components = panel_data
                    await inter.edit_original_message(content=None, embed=embed, components=components)
                else:
                    await inter.edit_original_message(**panel_data)

def setup(bot: commands.Bot):
    bot.add_cog(PainelCommand(bot))