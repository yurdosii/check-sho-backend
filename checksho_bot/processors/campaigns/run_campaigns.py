from datetime import datetime

from django_tgbot.types.update import Update

from campaigns.helpers import get_campaign_results, get_telegram_run_campaign_text
from checksho_bot.bot import TelegramBot
from checksho_bot.models import TelegramState
from utils.telegram import telegram_command


@telegram_command
def run_campaigns(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()

    # get campaigns
    telegram_user = state.telegram_user
    campaigns = telegram_user.user_campaigns

    # check campaigns
    if not campaigns:
        text = "No active campaigns, please create new campaign "
        text += "or set existing campaigns to be active to run"
        bot.sendMessage(chat_id, text)
        return

    # typing action
    bot.sendChatAction(chat_id, bot.CHAT_ACTION_TYPING)

    # record time
    now = datetime.now()
    now_formatted = now.strftime("%d/%m/%Y %H:%M:%S")

    # get campaigns results
    campaigns_results_text = []
    for campaign in campaigns:
        campaign_results = get_campaign_results(campaign)
        campaign_results_text = get_telegram_run_campaign_text(
            campaign, campaign_results, set_runtime=False
        )
        campaigns_results_text.append(campaign_results_text)

    # send start message
    text = "Result of running active campaigns:\n"
    text += f"*Run time*: {now_formatted}\n\n"
    bot.sendMessage(
        chat_id,
        text,
        parse_mode=bot.PARSE_MODE_MARKDOWN,
        disable_web_page_preview=True,  # disable link preview
    )

    # send campaigns results messages
    for campaign_results_text in campaigns_results_text:
        bot.sendMessage(
            chat_id,
            campaign_results_text,
            parse_mode=bot.PARSE_MODE_MARKDOWN,
            disable_web_page_preview=True,  # disable link preview
        )
