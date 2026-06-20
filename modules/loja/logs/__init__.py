from .purchase_logs import PurchaseLogsSystem

def setup(bot):
    bot.purchase_logs = PurchaseLogsSystem(bot)
