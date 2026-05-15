from core.config import settings
from telealert import TeleAlertBot

bot = TeleAlertBot(
    token=settings.API_TOKEN,
    chat_id=settings.CHAT_ID,
    service="xs-auth",
    app_mode=settings.APP_MODE,
)
