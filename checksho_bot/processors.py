from django_tgbot.decorators import processor
from django_tgbot.state_manager import message_types, update_types, state_types
from django_tgbot.types.update import Update
from .bot import state_manager
from .models import TelegramState
from .bot import TelegramBot

from django_tgbot.types.replykeyboardmarkup import ReplyKeyboardMarkup
from django_tgbot.types.keyboardbutton import KeyboardButton
from django_tgbot.types.inlinekeyboardmarkup import InlineKeyboardMarkup
from django_tgbot.types.inlinekeyboardbutton import InlineKeyboardButton


@processor(state_manager, from_states=state_types.All)
def hello_world(bot: TelegramBot, update: Update, state: TelegramState):
    bot.sendMessage(update.get_chat().get_id(), "Hello!")


@processor(state_manager, from_states=state_types.All)
def pes(bot: TelegramBot, update: Update, state: TelegramState):
    bot.sendMessage(update.get_chat().get_id(), "Pes")
