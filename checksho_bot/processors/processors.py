from collections import OrderedDict

from django_tgbot.decorators import processor
from django_tgbot.state_manager import message_types, update_types
from django_tgbot.types.update import Update

from checksho_bot.bot import TelegramBot, state_manager
from checksho_bot.models import TelegramState
from checksho_bot.processors import campaigns


BOT_AVAILABLE_COMMANDS = OrderedDict(
    {
        "/status": {
            "description": "Run active campaigns",
            "function": lambda *args, **kwargs: campaigns.run_campaigns.run_campaigns(
                *args, **kwargs
            ),
        },
        "/campaigns": {
            "description": "List campaigns",
            "function": lambda *args, **kwargs: campaigns.list_campaigns.list_campaigns(
                *args, **kwargs
            ),
        },
        "/runcampaign": {
            "description": "Manually select campaign to run",
            "function": lambda *args, **kwargs: campaigns.run_campaign.run_campaign(
                *args, **kwargs
            ),
        },
        "/addcampaign": {
            "description": "Add new campaign",
            "function": lambda *args, **kwargs: campaigns.add_campaign.add_campaign(
                *args, **kwargs
            ),
        },
        "/deletecampaign": {
            "description": "Delete campaign",
            "function": lambda *args, **kwargs: campaigns.delete_campaign.delete_campaign(
                *args, **kwargs
            ),
        },
    }
)

# https://django-tgbot.readthedocs.io/en/latest/processors/ - 'update_types'
state_manager.set_default_update_types(update_types.Message)


@processor(state_manager, message_types=[message_types.Text])
def main_preprocessor(bot: TelegramBot, update: Update, state: TelegramState):
    chat_id = update.get_chat().get_id()
    text = update.get_message().get_text()

    if text == "/help":
        handle_help_command(chat_id, bot, state)
    elif text == "/start":
        handle_start_command(chat_id, bot, state)
    elif text in BOT_AVAILABLE_COMMANDS:
        BOT_AVAILABLE_COMMANDS[text]["function"](bot, update, state)  # run command
    else:
        handle_wrong_command(chat_id, bot, state)


def handle_help_command(chat_id: str, bot: TelegramBot, state: TelegramState):
    command_items = BOT_AVAILABLE_COMMANDS.items()
    commands = [f"{k} - {v['description']}" for k, v in command_items]
    commands_text = "\n".join(commands)

    text = f"You can control me by sending these commands: \n\n{commands_text}"

    bot.sendMessage(chat_id, text)
    state.set_name("")


def handle_start_command(chat_id: str, bot: TelegramBot, state: TelegramState):
    """
    Hi, I'm CheckSho bot. I can help you automate monitoring goods from the online stores.

    All you need to start monitoring is to create some campaigns.
    Then, according to the campaign's schedule, I'll send you the results here.

    To keep things simple, you can create and configure campaigns via the web application
    and use the Telegram bot only as a way to get monitoring results.

    You can control me by sending these commands:
    """
    command_items = BOT_AVAILABLE_COMMANDS.items()
    commands = [f"{k} - {v['description']}" for k, v in command_items]
    commands_text = "\n".join(commands)

    text = "Hi, I'm CheckSho bot. I can help you automate monitoring goods from "
    text += "the online stores.\n\n"
    text += "All you need to start monitoring is to create some campaigns.\n"
    text += "Then, according to the campaign's schedule, I'll send you the results here.\n\n"
    text += "To keep things simple, you can create and configure campaigns via the web application "
    text += "and use the Telegram bot only as a way to get monitoring results.\n\n\n"
    text += f"You can control me by sending these commands: \n\n{commands_text}"

    bot.sendMessage(chat_id, text)
    state.set_name("")


def handle_wrong_command(chat_id: str, bot: TelegramBot, state: TelegramState):
    text = "Wrong command. Type /help to get list of available commands"

    bot.sendMessage(chat_id, text)
    state.set_name("")
