import disnake
from functions.database import database as db
from functions.emoji import emoji
from ..history import log_ticket_event


class ReviewView(disnake.ui.View):
    def __init__(self, ticket_channel_id: int, attendant_id: int = None):
        super().__init__(timeout=300)
        self.ticket_channel_id = ticket_channel_id
        self.attendant_id = attendant_id

    async def _save_review(self, inter: disnake.MessageInteraction, rating: int, label: str):
        tickets_data = db.get_document("tickets_data") or {}

        for panel_id, users in tickets_data.get("panels", {}).items():
            for user_id, tickets_list in users.items():
                for ticket in tickets_list:
                    if ticket.get("ticket_id") == self.ticket_channel_id:
                        ticket["review"] = {
                            "rating": rating,
                            "label": label,
                            "reviewer_id": inter.author.id,
                            "attendant_id": self.attendant_id,
                            "timestamp": int(disnake.utils.utcnow().timestamp())
                        }
                        db.save_document("tickets_data", tickets_data)
                        log_ticket_event(
                            self.ticket_channel_id,
                            "review",
                            inter.author.id,
                            {"rating": rating, "label": label}
                        )
                        break

        stars = "⭐" * rating
        await inter.response.edit_message(
            content=f"{emoji.correct} **Avaliação registrada!**\n\n{stars} — **{label}**\n\nObrigado pelo seu feedback!",
            view=None
        )

    @disnake.ui.button(label="😞 Ruim", style=disnake.ButtonStyle.red, row=0)
    async def ruim(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self._save_review(inter, 1, "Ruim")

    @disnake.ui.button(label="😐 Regular", style=disnake.ButtonStyle.grey, row=0)
    async def regular(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self._save_review(inter, 3, "Regular")

    @disnake.ui.button(label="😊 Bom", style=disnake.ButtonStyle.green, row=0)
    async def bom(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self._save_review(inter, 4, "Bom")

    @disnake.ui.button(label="🌟 Excelente", style=disnake.ButtonStyle.blurple, row=0)
    async def excelente(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self._save_review(inter, 5, "Excelente")


async def review(inter: disnake.MessageInteraction):
    tickets_data = db.get_document("tickets_data") or {}

    ticket_info = None
    for panel_id, users in tickets_data.get("panels", {}).items():
        for user_id, tickets_list in users.items():
            for ticket in tickets_list:
                if ticket.get("ticket_id") == inter.channel.id:
                    ticket_info = ticket
                    break
            if ticket_info:
                break
        if ticket_info:
            break

    if ticket_info and ticket_info.get("review"):
        existing = ticket_info["review"]
        stars = "⭐" * existing.get("rating", 0)
        await inter.response.send_message(
            f"{emoji.information} Este ticket já foi avaliado!\n\n{stars} — **{existing.get('label', 'N/A')}**",
            ephemeral=True
        )
        return

    attendant_id = ticket_info.get("assumed_by") if ticket_info else None

    view = ReviewView(inter.channel.id, attendant_id)
    await inter.response.send_message(
        f"⭐ **Avalie o atendimento!**\n\nComo foi sua experiência neste ticket?",
        view=view,
        ephemeral=True
    )
