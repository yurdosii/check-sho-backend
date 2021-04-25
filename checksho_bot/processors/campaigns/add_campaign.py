from enum import Enum

from django_tgbot.decorators import processor
from django_tgbot.state_manager import message_types, state_types
from django_tgbot.types.update import Update

from django_tgbot.types.replykeyboardmarkup import ReplyKeyboardMarkup
from django_tgbot.types.keyboardbutton import KeyboardButton
from django_tgbot.types.replykeyboardremove import ReplyKeyboardRemove
from django_tgbot.exceptions import ProcessFailure

from campaigns.models import CampaignInterval, Market
from campaigns import helpers as campaigns_helpers
from checksho_bot.bot import state_manager, TelegramBot
from checksho_bot.models import TelegramState
from utils.telegram import telegram_command
from utils.list import split_into_chunks
from utils.validators import is_campaign_item_url_is_valid


def add_campaign(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()

    # started adding campaign
    text = "Adding new campaign"
    bot.sendMessage(chat_id, text)

    # choose market
    markets = Market.objects.all()
    markets_buttons = list(map(lambda market: KeyboardButton.a(market.title), markets))
    markets_buttons_by_chunks = list(split_into_chunks(markets_buttons, 2))

    text = "Please choose market:"
    bot.sendMessage(
        chat_id,
        text,
        reply_markup=ReplyKeyboardMarkup.a(
            keyboard=markets_buttons_by_chunks,
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )

    # changing state
    state.set_name("add_campaign__market")


@processor(
    state_manager,
    from_states="add_campaign__market",
    success="add_campaign__title",
    fail=state_types.Keep,
    message_types=message_types.Text,
)
def add_campaign_market(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()
    title = update.get_message().get_text()

    # get markets titles
    markets = Market.objects.all()
    markets_titles = list(map(lambda market: market.title, markets))

    # check market
    if title in markets_titles:
        # proceed to campaign title
        text = "Thanks, next is campaign's title:"
        bot.sendMessage(chat_id, text, reply_markup=remove_keyboard_markup())

        # update state
        state.set_memory({"market_title": title})
        state.set_name("add_campaign__items")

    else:
        # keep this step
        text = "Use keyboard below please"
        bot.sendMessage(chat_id, text)
        raise ProcessFailure


@processor(
    state_manager,
    from_states="add_campaign__title",
    success="add_campaign__interval",
    message_types=message_types.Text,
)
def add_campaign_title(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()
    title = update.get_message().get_text()

    # TODO - check whether campaign with given title for current user already exists

    # title can be only text so save it in memory
    state.update_memory({"title": title})

    # proceed to campaign interval
    buttons = [[KeyboardButton.a(text=choice.value)] for choice in CampaignInterval]
    text = "Campaign's interval (how often campaign's notifications should be sent):"
    bot.sendMessage(
        chat_id,
        text,
        reply_markup=ReplyKeyboardMarkup.a(
            keyboard=buttons,
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


@processor(
    state_manager,
    from_states="add_campaign__interval",
    success="add_campaign_items",
    fail=state_types.Keep,
    message_types=message_types.Text,
)
def add_campaign_interval(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()
    interval = update.get_message().get_text()

    # check interval
    try:
        CampaignInterval(interval)
    except ValueError:
        # keep this step
        text = "Use keyboard below please"
        bot.sendMessage(chat_id, text)
        raise ProcessFailure

    # save interval in memory
    state.update_memory({"interval": interval})

    # proceed to campaign items
    buttons = [
        [KeyboardButton.a(text="One by one"), KeyboardButton.a(text="Many at once")]
    ]
    text = "Add campaign items:\n"
    text += "- one by one with details (like title, is active)\n"
    text += "- many at once providing only list of urls"
    bot.sendMessage(
        chat_id,
        text,
        reply_markup=ReplyKeyboardMarkup.a(
            keyboard=buttons,
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


@processor(
    state_manager,
    from_states="add_campaign_items",
    # success="add_campaign__items",
    fail=state_types.Keep,
    message_types=message_types.Text,
)
def add_campaign_items(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()
    text = update.get_message().get_text()

    # handle responses
    if text == "One by one":
        response = "Good choice! Let's start with item's URL:"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())
        state.set_name("add_campaign_item__url")
    elif text == "Many at once":
        response = "Incredible! Send me list of urls then:"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())
        state.set_name("add_campaign_item__urls")
    else:
        response = "Use keyboard below please"
        bot.sendMessage(chat_id, response)
        raise ProcessFailure


@processor(
    state_manager,
    from_states="add_campaign_item__url",
    success="add_campaign_item__title_choice",
    fail=state_types.Keep,
    message_types=message_types.Text,
)
def add_campaign_item_url(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()
    url = update.get_message().get_text()

    # check url
    memory = state.get_memory()
    market_title = memory.get("market_title")
    items = memory.get("items", [])
    is_valid, error_text = is_campaign_item_url_is_valid(url, market_title, items)
    if not is_valid:
        text = f"{error_text}. Please try again:"
        bot.sendMessage(chat_id, text)
        raise ProcessFailure

    # save url in memory
    items = memory.get("items")
    if items:
        items.append({"url": url})
    else:
        items = [{"url": url}]
    state.update_memory({"items": items})

    # proceed to campaign item title
    buttons = [
        [
            KeyboardButton.a(text="Custom title"),
            KeyboardButton.a(text="Title from item page"),
        ]
    ]
    text = "Campaign item's title:\n"
    text += "- set custom title\n"
    text += "- use title form item page"
    bot.sendMessage(
        chat_id,
        text,
        reply_markup=ReplyKeyboardMarkup.a(
            keyboard=buttons,
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


@processor(
    state_manager,
    from_states="add_campaign_item__title_choice",
    fail=state_types.Keep,
    message_types=message_types.Text,
)
def handle_campaign_item_title_choice(
    bot: TelegramBot, update: Update, state: TelegramState
):
    # get chat data
    chat_id = update.get_chat().get_id()
    text = update.get_message().get_text()

    # handle responses
    if text == "Custom title":
        response = "And your custom title will be:"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())
        state.set_name("add_campaign_item__title")
    elif text == "Use title from item page":
        # TODO - тут пропарси title
        response = "Great! So title will be:"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())
        state.set_name("")

        # set memory (get items[-1] and then update last with url)
    else:
        response = "Use keyboard below please"
        bot.sendMessage(chat_id, response)
        raise ProcessFailure


@processor(
    state_manager,
    from_states="add_campaign_item__title",
    success="add_campaign_item__finish_choice",
    message_types=message_types.Text,
)
def add_campaign_item_title(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()
    title = update.get_message().get_text()

    # title can be only text so save it in memory
    items = state.get_memory().get("items")
    items[-1]["title"] = title
    state.update_memory({"items": items})

    # proceed to finish choice
    buttons = [
        [
            KeyboardButton.a(text="Add more items"),
            KeyboardButton.a(text="Finish creating"),
        ]
    ]
    text = "Next:\n"
    text += "- add more items\n"
    text += "- finish"
    bot.sendMessage(
        chat_id,
        text,
        reply_markup=ReplyKeyboardMarkup.a(
            keyboard=buttons,
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


@processor(
    state_manager,
    from_states="add_campaign_item__finish_choice",
    # success="add_campaign_item__title",
    fail=state_types.Keep,
    message_types=message_types.Text,
)
def handle_campaign_item_finish_choice(
    bot: TelegramBot, update: Update, state: TelegramState
):
    # get chat data
    chat_id = update.get_chat().get_id()
    text = update.get_message().get_text()

    # handle responses
    if text == "Add more items":
        items = state.get_memory().get("items")
        response = "Existing items: \n"
        response += "\n".join(["- " + item["url"] for item in items]) + "\n\n"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())

        response = "New item's URL:"
        bot.sendMessage(chat_id, response)

        state.set_name("add_campaign_item__url")
    elif text == "Finish creating":
        # TODO
        response = "Great! So campaign with this data will be created:"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())
        state.set_name("")

        # TODO set memory (get items[-1] and then update last with url)
    else:
        response = "Use keyboard below please"
        bot.sendMessage(chat_id, response)
        raise ProcessFailure


@processor(
    state_manager,
    from_states="add_campaign_item__urls",
    success="add_campaign_item__urls_choice",
    fail=state_types.Keep,
    message_types=message_types.Text,
)
def add_campaign_item_urls(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()
    urls_raw = update.get_message().get_text()

    # check url
    urls = urls_raw.split("\n")
    urls = set(urls)

    memory = state.get_memory()
    market_title = memory.get("market_title")

    valid_urls = []
    invalid_urls_errors = []
    for url in urls:
        market = Market.objects.get(title=market_title)
        items = memory.get("items", [])

        is_valid, error_text = is_campaign_item_url_is_valid(url, market, items)
        if is_valid:
            valid_urls.append(url)
        else:
            invalid_urls_errors.append((url, error_text))

    # response
    if not invalid_urls_errors:
        # save items in memory
        urls_to_items = map(lambda url: {"url": url}, valid_urls)
        items.extend(urls_to_items)
        state.update_memory({"items": items})

        # send response
        text = "Thanks. URLs are valid"
        buttons = [
            [KeyboardButton.a(text="Add more urls"), KeyboardButton.a(text="Finish")]
        ]
        bot.sendMessage(
            chat_id,
            text,
            reply_markup=ReplyKeyboardMarkup.a(
                keyboard=buttons,
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
    else:
        text = ""
        if valid_urls:
            text += "Valid urls: \n"
            text += "\n".join([f"- '{url}'" for url in valid_urls]) + "\n\n"
        text += "Invalid urls: \n"
        text += "\n".join([f"- '{url[0]}' - {url[1]}" for url in invalid_urls_errors])
        bot.sendMessage(chat_id, text)

        text = "List contains invalid urls. Fix and send again:"
        bot.sendMessage(chat_id, text)
        raise ProcessFailure


@processor(
    state_manager,
    from_states="add_campaign_item__urls_choice",
    # success="add_campaign_item__urls_choice",
    fail=state_types.Keep,
    message_types=message_types.Text,
)
def handle_campaign_item_urls_choice(
    bot: TelegramBot, update: Update, state: TelegramState
):
    # get chat data
    chat_id = update.get_chat().get_id()
    text = update.get_message().get_text()

    # handle responses
    if text == "Add more urls":
        response = "Fine! Send me list of urls then:"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())
        state.set_name("add_campaign_item__urls")
    elif text == "Finish":
        memory = state.get_memory()
        campaign = campaigns_helpers.create_campaign_from_telegram(memory)

        response = "Great. Created campaign will be:" + campaign.telegram_format
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())
        state.set_name(state_types.Reset)
        state.set_name("")
        state.reset_memory()
    else:
        response = "Use keyboard below please"
        bot.sendMessage(chat_id, response)
        raise ProcessFailure


# HELPERS
@processor(
    state_manager,
    from_states=[
        "add_campaign__title",
        "add_campaign_item__url",
        "add_campaign_item__title",
    ],
    success=state_types.Keep,
    exclude_message_types=message_types.Text,
)
def text_only(bot, update, state):
    text = "I'd appreciate it if you answer in text format 😅"
    bot.sendMessage(update.get_chat().get_id(), text)


@processor(
    state_manager,
    from_states=[
        "add_campaign__market",
        "add_campaign__interval",
        "add_campaign_items",
    ],
    success=state_types.Keep,
    exclude_message_types=message_types.Text,
)
def keyboard_only(bot, update, state):
    text = "Use keyboard below please"
    bot.sendMessage(update.get_chat().get_id(), text)


def remove_keyboard_markup():
    return ReplyKeyboardRemove.a(remove_keyboard=True)
