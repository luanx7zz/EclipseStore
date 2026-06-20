import disnake
from disnake.ui import Modal, TextInput
from functions.database import database as db
from functions.emoji import emoji
from ..history import log_ticket_event


class TicketNoteModal(Modal):
    def __init__(self, existing_note: str = ""):
        components = [
            TextInput(
                label="Anotação do Ticket",
                custom_id="note_content",
                style=disnake.TextInputStyle.paragraph,
                placeholder="Digite sua anotação aqui... (visível apenas para atendentes)",
                value=existing_note,
                max_length=2000,
                required=True,
            )
        ]
        super().__init__(title="Anotações do Ticket", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        note_content = inter.text_values.get("note_content", "").strip()
        if not note_content:
            await inter.response.send_message(
                f"{emoji.wrong} A anotação não pode estar vazia.",
                ephemeral=True
            )
            return

        tickets_data = db.get_document("tickets_data") or {}

        ticket_found = False
        for panel_id, users in tickets_data.get("panels", {}).items():
            for user_id, tickets in users.items():
                for ticket in tickets:
                    if ticket.get("ticket_id") == inter.channel.id:
                        if "notes" not in ticket:
                            ticket["notes"] = []
                        ticket["notes"].append({
                            "author_id": inter.author.id,
                            "author_name": str(inter.author),
                            "content": note_content,
                            "timestamp": int(disnake.utils.utcnow().timestamp())
                        })
                        ticket_found = True
                        break
                if ticket_found:
                    break
            if ticket_found:
                break

        if ticket_found:
            db.save_document("tickets_data", tickets_data)
            log_ticket_event(
                inter.channel.id,
                "note_added",
                inter.author.id,
                {"note": note_content[:100]}
            )

        await inter.response.send_message(
            f"{emoji.correct} Anotação salva com sucesso! (visível apenas para atendentes)",
            ephemeral=True
        )

        try:
            await inter.channel.send(
                f"{emoji.pencil if hasattr(emoji, 'pencil') else '📝'} **Anotação adicionada** por {inter.author.mention}\n"
                f"||{note_content}||",
                allowed_mentions=disnake.AllowedMentions.none()
            )
        except Exception:
            pass


async def notes(inter: disnake.MessageInteraction):
    tickets_data = db.get_document("tickets_data") or {}

    existing_note = ""
    for panel_id, users in tickets_data.get("panels", {}).items():
        for user_id, tickets_list in users.items():
            for ticket in tickets_list:
                if ticket.get("ticket_id") == inter.channel.id:
                    all_notes = ticket.get("notes", [])
                    if all_notes:
                        last = all_notes[-1]
                        existing_note = last.get("content", "")
                    break

    await inter.response.send_modal(TicketNoteModal(existing_note))
