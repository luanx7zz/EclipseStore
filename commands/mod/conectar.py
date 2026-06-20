"""
Comando /conectar — gerencia conexão do bot em canais de voz.
Correção: debounce + cooldown exponencial para evitar loop de entrar/sair.
"""
import disnake
import asyncio
import time
import logging
from disnake.ext import commands
from functions.emoji import emoji
from functions.database import database as db
from functions.perms import perms
from functions.message import message, embed_message
from functions.utils import utils

logger = logging.getLogger("eclipse_store.conectar")

# Estado de reconexão por guild
_reconnect_cooldown: dict[int, float] = {}
_reconnect_attempts: dict[int, int] = {}
_reconnecting: dict[int, bool] = {}

COOLDOWN_SECONDS = 15
MAX_ATTEMPTS = 5
BACKOFF_BASE = 5


class ConectarCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_connection_status(self, guild_id: int = None) -> dict:
        connection_data = db.get_document("bot_connection") or {}
        channel_id = connection_data.get("channel_id")
        channel = None
        if channel_id:
            channel = self.bot.get_channel(int(channel_id))
        is_connected = False
        if channel and self.bot.voice_clients:
            for vc in self.bot.voice_clients:
                if vc.channel and vc.channel.id == int(channel_id):
                    if guild_id is None or vc.guild.id == guild_id:
                        is_connected = True
                        break
        return {"channel_id": channel_id, "channel": channel, "is_connected": is_connected}

    def ConectarComponents(self, inter) -> list:
        colors = db.get_document("custom_colors")
        primary_color_hex = colors.get("primary")
        container_kwargs = {}
        if primary_color_hex:
            container_kwargs["accent_colour"] = disnake.Colour(int(primary_color_hex.replace("#", ""), 16))
        connection = self._get_connection_status(inter.guild.id if inter.guild else None)
        channel = connection["channel"]
        is_connected = connection["is_connected"]
        channel_display = channel.mention if channel else "`Nenhum canal configurado`"
        connect_button_label = "Desconectar" if is_connected else "Conectar"
        connect_button_style = disnake.ButtonStyle.red if is_connected else disnake.ButtonStyle.green
        container = disnake.ui.Container(
            disnake.ui.TextDisplay(f"# {emoji.z0}{emoji.z1}{emoji.z2}{emoji.z3}{emoji.z4}\n-# **Gerenciar Conexão do Bot**"),
            disnake.ui.Separator(spacing=disnake.SeparatorSpacing.small),
            disnake.ui.TextDisplay(f"{emoji.voice} **Canal Atual:** {channel_display}"),
            disnake.ui.Separator(spacing=disnake.SeparatorSpacing.small),
            disnake.ui.ActionRow(
                disnake.ui.Button(label=connect_button_label, style=connect_button_style, emoji=emoji.voice, custom_id="Conectar_Toggle"),
                disnake.ui.Button(label="Editar Canal", style=disnake.ButtonStyle.blurple, emoji=emoji.edit, custom_id="Conectar_EditChannel"),
            ),
            **container_kwargs
        )
        return [container]

    def ConectarEmbed(self, inter):
        colors = db.get_document("custom_colors")
        primary_color_hex = colors.get("primary")
        connection = self._get_connection_status(inter.guild.id if inter.guild else None)
        channel = connection["channel"]
        is_connected = connection["is_connected"]
        channel_display = channel.mention if channel else "`Nenhum canal configurado`"
        embed = disnake.Embed(
            title=f"{emoji.z0}{emoji.z1}{emoji.z2}{emoji.z3}{emoji.z4} Gerenciar Conexão do Bot",
            description=f"{emoji.voice} **Canal Atual:** {channel_display}",
        )
        if primary_color_hex:
            embed.color = int(primary_color_hex.replace("#", ""), 16)
        connect_button_label = "Desconectar" if is_connected else "Conectar"
        connect_button_style = disnake.ButtonStyle.red if is_connected else disnake.ButtonStyle.green
        components = [
            disnake.ui.ActionRow(
                disnake.ui.Button(label=connect_button_label, style=connect_button_style, emoji=emoji.voice, custom_id="Conectar_Toggle"),
                disnake.ui.Button(label="Editar Canal", style=disnake.ButtonStyle.blurple, emoji=emoji.edit, custom_id="Conectar_EditChannel"),
            )
        ]
        return embed, components

    @commands.slash_command(
        name="conectar",
        description="Gerencia a conexão do bot em canais de voz.",
        guild_ids=[utils.obter_server_principal()],
    )
    async def conectar(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        if not await perms.check(inter.user.id):
            await inter.followup.send("Você não tem permissão para usar este comando", ephemeral=True)
            return
        mode = db.get_document("custom_mode").get("mode")
        if mode == "embed":
            embed, components = self.ConectarEmbed(inter)
            await inter.edit_original_response(content=None, embed=embed, components=components)
        else:
            await inter.edit_original_response(components=self.ConectarComponents(inter))

    @commands.slash_command(
        name="desconectar",
        description="Desconecta o bot do canal de voz imediatamente.",
        guild_ids=[utils.obter_server_principal()],
    )
    async def desconectar(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        if not await perms.check(inter.user.id):
            await inter.followup.send("Você não tem permissão para usar este comando.", ephemeral=True)
            return
        if not self.bot.voice_clients:
            await inter.followup.send("O bot não está conectado a nenhum canal de voz.", ephemeral=True)
            return
        guild_id = inter.guild.id if inter.guild else None
        for vc in list(self.bot.voice_clients):
            try:
                await vc.disconnect(force=True)
            except Exception:
                pass
        connection_data = db.get_document("bot_connection") or {}
        connection_data["session_connected"] = False
        db.save_document("bot_connection", connection_data)
        if guild_id:
            _reconnect_attempts.pop(guild_id, None)
            _reconnect_cooldown.pop(guild_id, None)
            _reconnecting.pop(guild_id, None)
        await inter.followup.send("Bot desconectado do canal de voz.", ephemeral=True)

    @commands.Cog.listener("on_button_click")
    async def Conectar_Button_Listener(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith("Conectar"):
            return
        custom_id = inter.component.custom_id
        if custom_id == "Conectar_Toggle":
            await self._handle_toggle_connection(inter)
        elif custom_id == "Conectar_EditChannel":
            await self._handle_edit_channel(inter)

    async def _handle_toggle_connection(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        connection = self._get_connection_status(inter.guild.id if inter.guild else None)
        channel_id = connection["channel_id"]
        is_connected = connection["is_connected"]
        if not channel_id:
            await inter.followup.send("Configure um canal primeiro usando o botão 'Editar Canal'", ephemeral=True)
            return
        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            await inter.followup.send("Canal não encontrado. Configure um novo canal.", ephemeral=True)
            return
        if not isinstance(channel, disnake.VoiceChannel):
            await inter.followup.send("O canal configurado não é um canal de voz.", ephemeral=True)
            return
        guild_id = inter.guild.id if inter.guild else None
        try:
            if is_connected:
                for vc in list(self.bot.voice_clients):
                    if vc.channel and vc.channel.id == channel.id:
                        await vc.disconnect(force=True)
                        break
                connection_data = db.get_document("bot_connection") or {}
                connection_data["session_connected"] = False
                db.save_document("bot_connection", connection_data)
                if guild_id:
                    _reconnect_attempts.pop(guild_id, None)
                    _reconnect_cooldown.pop(guild_id, None)
                    _reconnecting.pop(guild_id, None)
            else:
                for vc in list(self.bot.voice_clients):
                    try:
                        await vc.disconnect(force=True)
                    except Exception:
                        pass
                await channel.connect(timeout=10, reconnect=False)
                connection_data = db.get_document("bot_connection") or {}
                connection_data["session_connected"] = True
                db.save_document("bot_connection", connection_data)
                if guild_id:
                    _reconnect_attempts[guild_id] = 0
                    _reconnecting[guild_id] = False
        except Exception as e:
            error_msg = str(e)
            if "PyNaCl" in error_msg:
                await inter.followup.send("Erro: instale PyNaCl — `pip install PyNaCl`", ephemeral=True)
            else:
                await inter.followup.send(f"Erro ao {'desconectar' if is_connected else 'conectar'}: {error_msg}", ephemeral=True)
            return
        mode = db.get_document("custom_mode").get("mode")
        if mode == "embed":
            embed, components = self.ConectarEmbed(inter)
            await inter.edit_original_message(content=None, embed=embed, components=components)
        else:
            await inter.edit_original_message(components=self.ConectarComponents(inter))

    async def _handle_edit_channel(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        voice_channels = [ch for ch in inter.guild.channels if isinstance(ch, disnake.VoiceChannel)]
        if not voice_channels:
            await inter.followup.send("Não há canais de voz neste servidor.", ephemeral=True)
            return
        mode = db.get_document("custom_mode").get("mode")
        colors = db.get_document("custom_colors")
        primary_color_hex = colors.get("primary")
        if mode == "components":
            container_kwargs = {}
            if primary_color_hex:
                container_kwargs["accent_colour"] = disnake.Colour(int(primary_color_hex.replace("#", ""), 16))
            container = disnake.ui.Container(
                disnake.ui.TextDisplay(f"# {emoji.z0}{emoji.z1}{emoji.z2}{emoji.z3}{emoji.z4}\n-# **Selecionar Canal de Voz**"),
                disnake.ui.Separator(spacing=disnake.SeparatorSpacing.small),
                disnake.ui.TextDisplay(f"{emoji.information} Selecione o canal de voz onde o bot deve se conectar:"),
                disnake.ui.ActionRow(
                    disnake.ui.ChannelSelect(
                        placeholder="Selecione um canal de voz...",
                        custom_id="Conectar_SelectChannel",
                        channel_types=[disnake.ChannelType.voice],
                        min_values=1,
                        max_values=1,
                    )
                ),
                **container_kwargs
            )
            await inter.edit_original_message(components=[container])
        else:
            embed_kwargs = {}
            if primary_color_hex:
                embed_kwargs["color"] = int(primary_color_hex.replace("#", ""), 16)
            embed = disnake.Embed(
                title=f"{emoji.z0}{emoji.z1}{emoji.z2}{emoji.z3}{emoji.z4} Selecionar Canal de Voz",
                description=f"{emoji.information} Selecione o canal de voz onde o bot deve se conectar:",
                **embed_kwargs
            )
            components = [
                disnake.ui.ActionRow(
                    disnake.ui.ChannelSelect(
                        placeholder="Selecione um canal de voz...",
                        custom_id="Conectar_SelectChannel",
                        channel_types=[disnake.ChannelType.voice],
                        min_values=1,
                        max_values=1,
                    )
                )
            ]
            await inter.edit_original_message(content=None, embed=embed, components=components)

    @commands.Cog.listener("on_dropdown")
    async def Conectar_Dropdown_Listener(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "Conectar_SelectChannel":
            await inter.response.defer(ephemeral=True)
            channel_id = int(inter.values[0])
            channel = inter.guild.get_channel(channel_id)
            if not channel or not isinstance(channel, disnake.VoiceChannel):
                await inter.followup.send("Canal inválido.", ephemeral=True)
                return
            connection_data = db.get_document("bot_connection") or {}
            connection_data["channel_id"] = str(channel_id)
            db.save_document("bot_connection", connection_data)
            mode = db.get_document("custom_mode").get("mode")
            if mode == "embed":
                embed, components = self.ConectarEmbed(inter)
                await inter.edit_original_message(content=None, embed=embed, components=components)
            else:
                await inter.edit_original_message(components=self.ConectarComponents(inter))

    @commands.Cog.listener("on_voice_state_update")
    async def voice_state_auto_rejoin(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        """
        Reconecta ao canal de voz se o bot foi desconectado externamente.
        Usa debounce + backoff exponencial para NUNCA entrar em loop.
        """
        if member.id != self.bot.user.id:
            return

        connection_data = db.get_document("bot_connection") or {}
        if not connection_data.get("session_connected", False):
            return

        channel_id = connection_data.get("channel_id")
        if not channel_id:
            return

        # Só age quando o bot SAI de um canal sem ir para outro
        if not (before.channel is not None and after.channel is None):
            return

        guild_id = member.guild.id if member.guild else 0

        # Evitar múltiplos loops simultâneos para a mesma guild
        if _reconnecting.get(guild_id, False):
            return

        # Cooldown mínimo entre tentativas
        last_attempt = _reconnect_cooldown.get(guild_id, 0)
        now = time.time()
        if now - last_attempt < COOLDOWN_SECONDS:
            logger.debug(f"[Voz] Cooldown ativo para guild {guild_id}, ignorando reconexão.")
            return

        # Máximo de tentativas
        attempts = _reconnect_attempts.get(guild_id, 0)
        if attempts >= MAX_ATTEMPTS:
            logger.warning(
                f"[Voz] Máximo de {MAX_ATTEMPTS} tentativas atingido para guild {guild_id}. "
                f"Reconexão automática desativada. Use /conectar para reativar."
            )
            connection_data["session_connected"] = False
            try:
                db.save_document("bot_connection", connection_data)
            except Exception:
                pass
            _reconnect_attempts.pop(guild_id, None)
            _reconnecting.pop(guild_id, None)
            return

        _reconnecting[guild_id] = True
        _reconnect_cooldown[guild_id] = now
        _reconnect_attempts[guild_id] = attempts + 1

        wait_time = BACKOFF_BASE * (attempts + 1)
        logger.info(f"[Voz] Tentativa {attempts + 1}/{MAX_ATTEMPTS} em {wait_time}s (guild {guild_id})")

        try:
            await asyncio.sleep(wait_time)

            # Re-verificar estado após esperar
            connection_data = db.get_document("bot_connection") or {}
            if not connection_data.get("session_connected", False):
                return

            channel = self.bot.get_channel(int(channel_id))
            if not channel or not isinstance(channel, disnake.VoiceChannel):
                return

            already_connected = any(
                vc.channel and vc.channel.id == channel.id
                for vc in self.bot.voice_clients
            )
            if not already_connected:
                await channel.connect(timeout=15, reconnect=False)
                logger.info(f"[Voz] Reconectado: {channel.name} (guild {guild_id})")
                _reconnect_attempts[guild_id] = 0
        except asyncio.TimeoutError:
            logger.warning(f"[Voz] Timeout na reconexão (guild {guild_id})")
        except Exception as e:
            logger.warning(f"[Voz] Erro na reconexão tentativa {attempts + 1}: {e}")
        finally:
            _reconnecting[guild_id] = False


def setup(bot: commands.Bot):
    bot.add_cog(ConectarCommand(bot))
