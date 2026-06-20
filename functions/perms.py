from functions.database import database as db

class perms:
    @staticmethod
    async def check(user_id) -> bool:
        config = db.obter("config.json")
        perms = config["bot"]["perms"]
        return str(user_id) in perms

    @staticmethod
    async def check_owner(user_id) -> bool:
        config = db.obter("config.json")
        owner = config["bot"]["owner"]
        return str(user_id) == owner