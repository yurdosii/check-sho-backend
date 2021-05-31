from enum import Enum

from django.conf import settings
from django.db.models import QuerySet
from django_tgbot.decorators import processor
from django_tgbot.state_manager import state_types, update_types
from django_tgbot.types.inlinekeyboardbutton import InlineKeyboardButton
from django_tgbot.types.inlinekeyboardmarkup import InlineKeyboardMarkup
from django_tgbot.types.update import Update

from campaigns.helpers import get_telegram_get_campaign_text
from checksho_bot.bot import TelegramBot, state_manager
from checksho_bot.models import TelegramState
from utils.telegram import telegram_command

from ..utils import get_navigation_buttons, get_paginator_and_pages


class ListCampaignsState(Enum):
    CALLBACK = "list_campaigns__callback"


def get_text_and_buttons(campaigns: QuerySet, page: int):
    p, previous_page, next_page = get_paginator_and_pages(
        campaigns, page, per_page=1, order_by=None
    )

    campaign = p.page(page).object_list[0]
    text = get_telegram_get_campaign_text(campaign)

    buttons = []

    navigation_buttons = get_navigation_buttons(
        page, previous_page, next_page, p.num_pages
    )
    get_all_campaigns_button = [
        InlineKeyboardButton.a("Get all campaigns", callback_data="all")
    ]
    stop_scrolling_button = [
        InlineKeyboardButton.a("Stop scrolling", callback_data="stop")
    ]

    buttons.append(navigation_buttons)
    buttons.append(get_all_campaigns_button)
    buttons.append(stop_scrolling_button)

    return text, buttons


@telegram_command
def list_campaigns(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()

    # get campaigns
    telegram_user = state.telegram_user
    campaigns = telegram_user.user_campaigns

    # check campaigns
    if not campaigns:
        text = "No campaigns was created. "
        text += "You can create a campaign using /addcampaign command "

        # when localhost - it won't show as link
        if "localhost" not in settings.CLIENT_URL:
            text += f"or on [web application]({settings.CLIENT_URL})"

        bot.sendMessage(
            chat_id,
            text,
            parse_mode=bot.PARSE_MODE_MARKDOWN,
            disable_web_page_preview=True,  # disable link preview
        )
        return

    # save page
    state.update_memory({"page": 1})

    # send response
    text, buttons = get_text_and_buttons(campaigns, 1)
    bot.sendMessage(
        chat_id,
        text,
        parse_mode=bot.PARSE_MODE_MARKDOWN,
        reply_markup=InlineKeyboardMarkup.a(inline_keyboard=buttons),
    )

    # changing state
    state.set_name(ListCampaignsState.CALLBACK.value)


@processor(
    state_manager,
    from_states=ListCampaignsState.CALLBACK.value,
    update_types=[update_types.CallbackQuery],
)
def handle_callback_query(bot: TelegramBot, update, state):
    # get data
    chat_id = update.get_chat().get_id()
    callback_data = update.get_callback_query().get_data()
    message_id = update.get_callback_query().message.message_id

    # handle callback data
    if "#" in callback_data:
        # change page

        # check page
        page = int(callback_data[1:])
        if page == state.get_memory().get("page"):
            return

        # save page
        state.update_memory({"page": page})

        # get campaigns
        telegram_user = state.telegram_user
        campaigns = telegram_user.user_campaigns

        # send response
        text, buttons = get_text_and_buttons(campaigns, page)
        bot.editMessageText(
            text,
            chat_id,
            message_id,
            parse_mode=bot.PARSE_MODE_MARKDOWN,
            reply_markup=InlineKeyboardMarkup.a(inline_keyboard=buttons),
            disable_webpage_preview=True,  # disable link preview # TODO - doesn't work
        )

        # change state
        state.set_name(ListCampaignsState.CALLBACK.value)

    elif callback_data == "all":
        # show all campaigns at once

        # TODO - if message is long, it won't show markdown, so split it by 4 campaigns
        # and send a lot of messages

        # get campaigns
        telegram_user = state.telegram_user
        campaigns = telegram_user.user_campaigns

        # get campaign data
        sep = "#" * 30
        campaigns_length = len(campaigns)
        text = "Your campaigns:\n\n"

        for i, campaign in enumerate(campaigns):
            campaign_text = get_telegram_get_campaign_text(campaign)
            text += campaign_text
            text += "\n"

            if i != campaigns_length - 1:
                text += sep

            text += "\n\n\n"

        # send response
        bot.sendMessage(
            chat_id,
            text,
            parse_mode=bot.PARSE_MODE_MARKDOWN,
            disable_web_page_preview=True,  # disable link preview
        )

        # change state
        state.set_name("")

        # reset memory
        state.reset_memory()

    else:
        # change state to default (to be commands are only available)

        # send response
        text = "Scrolling was stopped, you can continue using commands as usual"
        bot.sendMessage(
            chat_id,
            text,
            parse_mode=bot.PARSE_MODE_MARKDOWN,
            disable_web_page_preview=True,  # disable link preview
        )

        # change state
        state.set_name("")

        # reset memory
        state.reset_memory()


@processor(
    state_manager,
    from_states=ListCampaignsState.CALLBACK.value,
    success=state_types.Keep,
    exclude_update_types=[update_types.CallbackQuery],
)
def callback_only(bot, update, state):
    text = "Please use buttons in message"
    bot.sendMessage(update.get_chat().get_id(), text)
