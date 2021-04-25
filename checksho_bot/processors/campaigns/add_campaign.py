from enum import Enum

from checksho_bot.bot import TelegramBot, state_manager
from checksho_bot.models import TelegramState
from django_tgbot.decorators import processor
from django_tgbot.exceptions import ProcessFailure
from django_tgbot.state_manager import message_types, state_types
from django_tgbot.types.keyboardbutton import KeyboardButton
from django_tgbot.types.replykeyboardmarkup import ReplyKeyboardMarkup
from django_tgbot.types.replykeyboardremove import ReplyKeyboardRemove
from django_tgbot.types.update import Update
from utils.list import split_into_chunks
from utils.telegram import telegram_command
from utils.validators import is_campaign_item_url_is_valid

from campaigns import helpers as campaigns_helpers
from campaigns.models import CampaignInterval, Market

# Important notes
# - user cannot edit what he already wrote in the end (for now)


class AddCampaignButton(Enum):
    ITEMS_ONE_BY_ONE = "One by one"
    ITEMS_MANY_AT_ONCE = "Many at once"
    ITEM_CUSTOM_TITLE = "Custom title"
    ITEM_TITLE_FROM_PAGE = "Title from item page"
    ADD_MORE_ITEMS = "Add more items"
    FINISH = "Finish"
    ADD_MORE_URLS = "Add more urls"


class AddCampaignState(Enum):
    MARKET = "add_campaign__market"
    TITLE = "add_campaign__title"
    INTERVAL = "add_campaign__interval"
    ITEMS = "add_campaign__items"


class AddItemState(Enum):
    URL = "add_campaign_item__url"
    URLS = "add_campaign_item__urls"
    TITLE_CHOICE = "add_campaign_item__title_choice"
    TITLE = "add_campaign_item__title"
    FINISH_CHOICE = "add_campaign_item__finish_choice"

    URLS_CHOICE = "add_campaign_item__urls_choice"


@telegram_command
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

    # send response
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
    state.set_name(AddCampaignState.MARKET.value)


@processor(
    state_manager,
    from_states=AddCampaignState.MARKET.value,
    success=AddCampaignState.TITLE.value,
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

    else:
        # keep this step
        text = "Use keyboard below please"
        bot.sendMessage(chat_id, text)
        raise ProcessFailure


@processor(
    state_manager,
    from_states=AddCampaignState.TITLE.value,
    success=AddCampaignState.INTERVAL.value,
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
    from_states=AddCampaignState.INTERVAL.value,
    success=AddCampaignState.ITEMS.value,
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
    text = "Add campaign items:\n"
    text += "- one by one with details (like title, is active)\n"
    text += "- many at once providing only list of urls"
    buttons = [
        [
            KeyboardButton.a(text=AddCampaignButton.ITEMS_ONE_BY_ONE.value),
            KeyboardButton.a(text=AddCampaignButton.ITEMS_MANY_AT_ONCE.value),
        ]
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


@processor(
    state_manager,
    from_states=AddCampaignState.ITEMS.value,
    fail=state_types.Keep,
    message_types=message_types.Text,
)
def add_campaign_items(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()
    text = update.get_message().get_text()

    # handle responses
    if text == AddCampaignButton.ITEMS_ONE_BY_ONE.value:
        response = "Good choice! Let's start with item's URL:"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())
        state.set_name(AddItemState.URL.value)

    elif text == AddCampaignButton.ITEMS_MANY_AT_ONCE.value:
        response = "Incredible! Send me list of urls then:"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())
        state.set_name(AddItemState.URLS.value)

    else:
        response = "Use keyboard below please"
        bot.sendMessage(chat_id, response)
        raise ProcessFailure


@processor(
    state_manager,
    from_states=AddItemState.URL.value,
    success=AddItemState.TITLE_CHOICE.value,
    fail=state_types.Keep,
    message_types=message_types.Text,
)
def add_campaign_item_url(bot: TelegramBot, update: Update, state: TelegramState):
    # TODO - щоб було підтвердження, типу людина ввела url,
    # TODO - я виводжу назву і ціну і він підтверджує

    # get chat data
    chat_id = update.get_chat().get_id()
    url = update.get_message().get_text()

    # check url
    memory = state.get_memory()
    market_title = memory.get("market_title")
    market = Market.objects.get(title=market_title)
    items = memory.get("items", [])

    is_valid, error_text = is_campaign_item_url_is_valid(url, market, items)
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
    text = "Campaign item's title:\n"
    text += "- set custom title\n"
    text += "- use title form item page"
    buttons = [
        [
            KeyboardButton.a(text=AddCampaignButton.ITEM_CUSTOM_TITLE.value),
            KeyboardButton.a(text=AddCampaignButton.ITEM_TITLE_FROM_PAGE.value),
        ]
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


@processor(
    state_manager,
    from_states=AddItemState.TITLE_CHOICE.value,
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
    if text == AddCampaignButton.ITEM_CUSTOM_TITLE.value:
        response = "And your custom title will be:"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())
        state.set_name(AddItemState.TITLE.value)

    elif text == AddCampaignButton.ITEM_TITLE_FROM_PAGE.value:
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
    from_states=AddItemState.TITLE.value,
    success=AddItemState.FINISH_CHOICE.value,
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
    text = "Next:\n"
    text += "- add more items\n"
    text += "- finish"
    buttons = [
        [
            KeyboardButton.a(text=AddCampaignButton.ADD_MORE_ITEMS.value),
            KeyboardButton.a(text=AddCampaignButton.FINISH.value),
        ]
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


@processor(
    state_manager,
    from_states=AddItemState.FINISH_CHOICE.value,
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
    if text == AddCampaignButton.ADD_MORE_ITEMS.value:
        # TODO - should return to choice one by one / many at once
        # TODO - add new function that returns this choice and change state here

        # output existing items
        items = state.get_memory().get("items")
        response = "Existing items: \n"
        response += "\n".join(["- " + item["url"] for item in items]) + "\n\n"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())

        # output ask for new item
        response = "New item's URL:"
        bot.sendMessage(chat_id, response)

        # update state
        state.set_name(AddItemState.URL.value)

    elif text == AddCampaignButton.FINISH.value:
        # TODO - дублюється

        # create campaign
        memory = state.get_memory()
        campaign = campaigns_helpers.create_campaign_from_telegram(memory)

        # send campaign's data
        response = "Great! So campaign with this data was created:"
        response += campaign.telegram_format
        bot.sendMessage(
            chat_id,
            response,
            reply_markup=remove_keyboard_markup(),
            parse_mode=bot.PARSE_MODE_MARKDOWN,
        )

        # update state and memory
        state.set_name("")
        state.reset_memory()

    else:
        # keep this step
        response = "Use keyboard below please"
        bot.sendMessage(chat_id, response)
        raise ProcessFailure


@processor(
    state_manager,
    from_states=AddItemState.URLS.value,
    success=AddItemState.URLS_CHOICE.value,
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
            [
                KeyboardButton.a(text=AddCampaignButton.ADD_MORE_URLS.value),
                KeyboardButton.a(text=AddCampaignButton.FINISH.value),
            ]
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
        # send list of valid and invalid urls
        text = ""
        if valid_urls:
            text += "Valid urls: \n"
            text += "\n".join([f"- '{url}'" for url in valid_urls]) + "\n\n"
        text += "Invalid urls: \n"
        text += "\n".join([f"- '{url[0]}' - {url[1]}" for url in invalid_urls_errors])
        bot.sendMessage(chat_id, text)

        # ask for urls list to be resent
        text = "List contains invalid urls. Fix and send again:"
        bot.sendMessage(chat_id, text)
        raise ProcessFailure


@processor(
    state_manager,
    from_states=AddItemState.URLS_CHOICE.value,
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
    if text == AddCampaignButton.ADD_MORE_URLS.value:
        response = "Fine! Send me list of urls then:"
        bot.sendMessage(chat_id, response, reply_markup=remove_keyboard_markup())
        state.set_name(AddItemState.URLS.value)

    elif text == AddCampaignButton.FINISH.value:
        # TODO - дублюється

        # create campaign
        memory = state.get_memory()
        campaign = campaigns_helpers.create_campaign_from_telegram(memory)

        # send campaign's data
        response = "Great! So campaign with this data was created:"
        response += campaign.telegram_format
        bot.sendMessage(
            chat_id,
            response,
            reply_markup=remove_keyboard_markup(),
            parse_mode=bot.PARSE_MODE_MARKDOWN,
        )

        # update state and memory
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
        AddCampaignState.TITLE.value,
        AddItemState.URL.value,
        AddItemState.TITLE.value,
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
        AddCampaignState.MARKET.value,
        AddCampaignState.INTERVAL.value,
        AddCampaignState.ITEMS.value,
    ],
    success=state_types.Keep,
    exclude_message_types=message_types.Text,
)
def keyboard_only(bot, update, state):
    text = "Use keyboard below please"
    bot.sendMessage(update.get_chat().get_id(), text)


def remove_keyboard_markup():
    return ReplyKeyboardRemove.a(remove_keyboard=True)
