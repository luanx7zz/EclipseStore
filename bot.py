import core
from functions.emojis import emojis
from functions.database import database
from functions.utils import utils
from functions.emoji import init_on_startup
from core.server_protection import apply_server_protection

bot, token, id = core.create_bot()

database.initialize_database_if_needed()
database.verify_and_create_missing_documents()

init_on_startup(token, id)

# Proteção de servidor
apply_server_protection(bot)

###########################################################

bot.load_extension("modules")
bot.load_extension("commands")
bot.load_extension("events")
bot.load_extension("tasks")

if __name__ == "__main__":
    core.change_bio()
    core.enable_intents(token, id)  # CORREÇÃO AQUI
    bot.run(token)