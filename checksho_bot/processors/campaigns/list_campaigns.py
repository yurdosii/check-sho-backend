from checksho_bot.bot import TelegramBot
from checksho_bot.models import TelegramState
from django_tgbot.types.update import Update
from utils.telegram import telegram_command

from campaigns.models import Campaign


@telegram_command
def list_campaigns(bot: TelegramBot, update: Update, state: TelegramState):
    # TODO - той слайдер це кароче через колбеки кнопки, прикольно (через InlineKeyboardButton)

    # TODO - треба тут слайдер той (походу ті музики це просто кнопки stacked якось, але хз точно)
    # TODO - URL зробити як URL як link, а не як зараз і тоді гарніше буде

    # get chat data
    chat_id = update.get_chat().get_id()

    # get list of campaigns in telegram format
    campaigns = Campaign.objects.all()
    campaigns_text = [campaign.telegram_format for campaign in campaigns]
    sep = "-" * 80 + "\n"
    text = sep.join(campaigns_text)

    # send response
    bot.sendMessage(chat_id, text, parse_mode=bot.PARSE_MODE_MARKDOWN)

    # changing state
    state.set_name("")
