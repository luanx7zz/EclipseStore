from disnake.ext import commands
import disnake

from functions.emoji import emoji
from functions.message import message, embed_message
from functions.database import database as db

class Loja(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def panel(self, inter: disnake.MessageInteraction):
        mode = db.get_document("custom_mode").get("mode")
        if mode == "embed":
            return self._panel_embed(inter)
        return self._panel_components(inter)

    def _panel_components(self, inter: disnake.MessageInteraction) -> dict:
        color_data = db.get_document("custom_colors")
        primary_color_hex = color_data.get("primary")

        container_kwargs = {}
        if primary_color_hex:
            container_kwargs["accent_colour"] = disnake.Colour(int(primary_color_hex.replace("#", ""), 16))

        options = [
            disnake.SelectOption(label="Gerenciar Produtos", value="produtos", emoji=emoji.cardbox, description="Crie, Configure e Edite seus produtos."),
            disnake.SelectOption(label="Personalizar Loja", value="personalizar", emoji=emoji.edit, description="Personalize sua loja com criatividade."),
            disnake.SelectOption(label="Preferências", value="preferencias", emoji=emoji.settings2, description="Configure preferências do seu sistema de loja."),
            disnake.SelectOption(label="VIPs", value="vip", emoji=emoji.shield_star, description="Configure o sistema de VIPs da loja"),
            disnake.SelectOption(label="Configurar Clientes", value="clientes", emoji=emoji.members, description="Configure o sistema de clientes e condecorações"),
            #disnake.SelectOption(label="Gerenciar Gifts (Em breve)", value="gifts", emoji=emoji.gift2, description="Opção em desenvolvimento final"),
            disnake.SelectOption(label="Sistema de Saldo", value="saldo", emoji=emoji.wallet, description="Configure o sistema de saldo para sua loja."),
            disnake.SelectOption(label="Cashback", value="cashback", emoji=emoji.bank, description="Configure o sistema de cashback para sua loja."),
            disnake.SelectOption(label="Afiliados (Em breve)", value="afiliados", emoji=emoji.dollar, description="Opção em desenvolvimento final"),
            disnake.SelectOption(label="Eclipse Marketplace (Em breve)", value="sync_market", emoji=emoji.basket, description="Opção em desenvolvimento final"),
        ]

        return {"components": [
            disnake.ui.Container(
                disnake.ui.TextDisplay(f"# {emoji.z0}{emoji.z1}{emoji.z2}{emoji.z3}{emoji.z4}\n-# Painel > **Loja**"),
                disnake.ui.Separator(),
                disnake.ui.TextDisplay(f"Configure a sua loja selecionando uma seção abaixo.\nPara configurar as formas de pagamento, acesse as configurações."),
                disnake.ui.Separator(),
                disnake.ui.ActionRow(
                    disnake.ui.StringSelect(
                        custom_id="Loja_Select",
                        placeholder="Selecione uma seção para configurar",
                        options=options,
                    )
                ),
                disnake.ui.TextDisplay(f"-# Alguns sistemas deste painel ainda não foram implementados.\n-# Aguarde a próxima versão para utilizar essas funcionalidades."),
                **container_kwargs
            ),
            disnake.ui.ActionRow(disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="PainelInicial")),
        ]}

    def _panel_embed(self, inter: disnake.MessageInteraction) -> dict:
        color_data = db.get_document("custom_colors")
        primary_color_hex = color_data.get("primary")

        embed_kwargs = {}
        if primary_color_hex:
            embed_kwargs["color"] = int(primary_color_hex.replace("#", ""), 16)

        embed = disnake.Embed(
            # title=f"Configurar Loja",
            description=f"-# Painel > **Configurar Loja**\n\nConfigure a sua loja selecionando uma seção abaixo.\nPara configurar as formas de pagamento, acesse as configurações.",
            **embed_kwargs
        )

        options = [
            disnake.SelectOption(label="Gerenciar Produtos", value="produtos", emoji=emoji.cardbox, description="Crie, Configure e Edite seus produtos."),
            disnake.SelectOption(label="Personalizar Loja", value="personalizar", emoji=emoji.edit, description="Personalize sua loja com criatividade."),
            disnake.SelectOption(label="Preferências", value="preferencias", emoji=emoji.settings2, description="Configure preferências do seu sistema de loja."),
            #disnake.SelectOption(label="Vip (Em breve)", value="vip", emoji=emoji.fire, description="Opção em desenvolvimento final"),
            disnake.SelectOption(label="Configurar Clientes", value="clientes", emoji=emoji.members, description="Configure o sistema de clientes e condecorações"),
            #disnake.SelectOption(label="Gerenciar Gifts (Em breve)", value="gifts", emoji=emoji.gift2, description="Opção em desenvolvimento final"),
            disnake.SelectOption(label="Sistema de Saldo", value="saldo", emoji=emoji.wallet, description="Configure o sistema de saldo para sua loja."),
            disnake.SelectOption(label="Cashback", value="cashback", emoji=emoji.bank, description="Configure o sistema de cashback para sua loja."),
            disnake.SelectOption(label="Afiliados (Em breve)", value="afiliados", emoji=emoji.dollar, description="Opção em desenvolvimento final"),
            disnake.SelectOption(label="Eclipse Marketplace (Em breve)", value="sync_market", emoji=emoji.basket, description="Opção em desenvolvimento final"),
        ]

        components = [
            disnake.ui.ActionRow(
                disnake.ui.StringSelect(
                    custom_id="Loja_Select",
                    placeholder="Selecione uma seção para configurar",
                    options=options,
                )
            ),
            disnake.ui.ActionRow(disnake.ui.Button(label="Voltar", style=disnake.ButtonStyle.grey, emoji=emoji.back, custom_id="PainelInicial")),
        ]
        return {"embed": embed, "components": components}

    @commands.Cog.listener("on_button_click")
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "Painel_Loja":
            mode = db.get_document("custom_mode").get("mode")
            msg_handler = embed_message if mode == "embed" else message
            await msg_handler.wait(inter, send=False)

            panel_data = self.panel(inter)
            if "embed" in panel_data:
                await inter.edit_original_message(content=None, **panel_data)
            else:
                await inter.edit_original_message(**panel_data, flags=disnake.MessageFlags(is_components_v2=True))
        
        elif inter.component.custom_id == "Loja_Panel":
            mode = db.get_document("custom_mode").get("mode")
            msg_handler = embed_message if mode == "embed" else message
            await msg_handler.wait(inter, send=False)

            panel_data = self.panel(inter)
            if "embed" in panel_data:
                await inter.edit_original_message(content=None, **panel_data)
            else:
                await inter.edit_original_message(**panel_data, flags=disnake.MessageFlags(is_components_v2=True))

    @commands.Cog.listener("on_dropdown")
    async def on_dropdown(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "Loja_Select":
            choice = inter.values[0]

            # Itens em breve
            coming_soon = {
                "gifts", "afiliados", "sync_market"
            }

            if choice in coming_soon:
                await inter.response.send_message(
                    "Essa funcionalidade será implementada em breve em próximas atualizações.",
                    ephemeral=True
                )
                return

            mode = db.get_document("custom_mode").get("mode")
            msg_handler = embed_message if mode == "embed" else message
            await msg_handler.wait(inter, send=False)

            if choice == "produtos":
                from .products.cog import GerenciarProdutos
                panel_data = GerenciarProdutos(self.bot).panel(inter)
            elif choice == "personalizar":
                from .personalization.cog import PersonalizarLoja
                panel_data = PersonalizarLoja.panel(inter)
            elif choice == "preferencias":
                from .preferences.cog import PreferenciasLoja
                panel_data = PreferenciasLoja.panel(inter)
            elif choice == "clientes":
                from .clientes.cog import ClientesSystem
                clientes_system = ClientesSystem(self.bot)
                panel_data = clientes_system.panel_clientes(inter)
            elif choice == "saldo":
                from .saldo.cog import SaldoSystem
                saldo_system = SaldoSystem(self.bot)
                panel_data = saldo_system.panel(inter)
            elif choice == "vip":
                from .vips.cog import panel_components as vip_comp, panel_embed as vip_emb
                panel_data = vip_emb(inter) if mode == "embed" else vip_comp(inter)
            elif choice == "cashback":
                from .cashback.cog import CashbackSystem
                cashback_system = CashbackSystem(self.bot)
                panel_data = cashback_system.panel(inter)
            else:
                panel_data = self.panel(inter)

            if isinstance(panel_data, tuple):
                embed, components = panel_data
                await inter.edit_original_message(content=None, embed=embed, components=components)
            elif "embed" in panel_data:
                await inter.edit_original_message(content=None, **panel_data)
            else:
                await inter.edit_original_message(**panel_data, flags=disnake.MessageFlags(is_components_v2=True))

def setup(bot: commands.Bot):
    bot.add_cog(Loja(bot))