from checksho_bot.bot import TelegramBot, state_manager
from checksho_bot.models import TelegramState
from checksho_bot.processors.campaigns.add_campaign import add_campaign
from django_tgbot.decorators import processor
from django_tgbot.state_manager import message_types
from django_tgbot.types.update import Update
from utils.telegram import telegram_command

from campaigns.models import Campaign

BOT_AVAILABLE_COMMANDS = {  # 'command': 'state name'
    "/addcampaign": {
        "description": "Add new campaign",
        "function": lambda *args, **kwargs: add_campaign(*args, **kwargs),
    },
    "/status": {
        "description": "Run active campaigns",
        "function": lambda *args, **kwargs: check_status(*args, **kwargs),
    }
    # run selected command
}


@processor(state_manager, message_types=[message_types.Text])
def main_preprocessor(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    text = update.get_message().get_text()

    if text == "/help":
        handle_help_command(chat_id, bot, state)
    elif text in BOT_AVAILABLE_COMMANDS:
        BOT_AVAILABLE_COMMANDS[text]["function"](bot, update, state)  # run command
    else:
        handle_wrong_command(chat_id, bot, state)


def handle_help_command(chat_id: str, bot: TelegramBot, state: TelegramState):
    # TODO - add headers like 'Campaigns:' and then list of commands that are related to campaigns
    command_items = BOT_AVAILABLE_COMMANDS.items()
    commands = [f"{k} - {v['description']}" for k, v in command_items]
    commands_text = "\n".join(commands)

    text = f"You can control me by sending these commands: \n\n{commands_text}"

    bot.sendMessage(chat_id, text)
    state.set_name("")


def handle_wrong_command(chat_id: str, bot: TelegramBot, state: TelegramState):
    text = "Wrong command. Type /help to get list of avaialable commands"

    bot.sendMessage(chat_id, text)
    state.set_name("")


@telegram_command
def check_status(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()

    text = "Running campaign"
    message = bot.sendMessage(chat_id, text)

    for _ in range(3):
        text += "."
        bot.editMessageText(text, chat_id, message.message_id)

    bot.editMessageText("Result: ", chat_id, message.message_id)
