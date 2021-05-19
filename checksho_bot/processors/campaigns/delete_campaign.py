from enum import Enum

from django_tgbot.decorators import processor
from django_tgbot.exceptions import ProcessFailure
from django_tgbot.state_manager import message_types, state_types, update_types
from django_tgbot.types.inlinekeyboardbutton import InlineKeyboardButton
from django_tgbot.types.inlinekeyboardmarkup import InlineKeyboardMarkup
from django_tgbot.types.keyboardbutton import KeyboardButton
from django_tgbot.types.replykeyboardmarkup import ReplyKeyboardMarkup
from django_tgbot.types.update import Update

from campaigns.models import Campaign
from checksho_bot.bot import TelegramBot, state_manager
from checksho_bot.models import TelegramState
from utils.telegram import telegram_command

from ..utils import (
    get_navigation_buttons,
    get_paginator_and_pages,
    remove_keyboard_markup,
)


class DeleteCampaignState(Enum):
    CALLBACK = "delete_campaign__callback"
    CONFIRMATION = "delete_campaign__confirmation"


def get_campaigns_buttons(page: int):
    p, previous_page, next_page = get_paginator_and_pages(
        page, per_page=5, order_by="title"
    )

    campaigns_by_page = p.page(page).object_list
    campaigns_buttons = list(
        map(
            lambda campaign: (
                [InlineKeyboardButton.a(campaign.title, callback_data=str(campaign.id))]
            ),
            campaigns_by_page,
        )
    )

    navigation_buttons = get_navigation_buttons(
        page, previous_page, next_page, p.num_pages
    )
    campaigns_buttons.append(navigation_buttons)

    return campaigns_buttons


@telegram_command
def delete_campaign(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()

    # save page
    state.update_memory({"page": 1})

    # send response
    campaigns_buttons = get_campaigns_buttons(1)
    text = "Select campaign to delete:"
    bot.sendMessage(
        chat_id,
        text,
        parse_mode=bot.PARSE_MODE_MARKDOWN,
        reply_markup=InlineKeyboardMarkup.a(inline_keyboard=campaigns_buttons),
    )

    # changing state
    state.set_name(DeleteCampaignState.CALLBACK.value)


@processor(
    state_manager,
    from_states=DeleteCampaignState.CALLBACK.value,
    fail="",
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

        page = int(callback_data[1:])
        if page == state.get_memory().get("page"):
            return

        # save page
        state.update_memory({"page": page})

        # send response
        campaigns_buttons = get_campaigns_buttons(page)
        bot.editMessageText(
            "Select campaign to delete:",
            chat_id,
            message_id,
            parse_mode=bot.PARSE_MODE_MARKDOWN,
            reply_markup=InlineKeyboardMarkup.a(inline_keyboard=campaigns_buttons),
        )

        # change state
        state.set_name(DeleteCampaignState.CALLBACK.value)

    else:
        # delete confirmation

        # check campaign
        campaign = Campaign.objects.filter(id=callback_data).first()
        if not campaign:
            text = "Selected campaign didn't exist, please try to delete later"
            bot.sendMessage(chat_id, text)
            raise ProcessFailure

        # save to memory
        state.update_memory({"campaign_id": callback_data})

        # send response
        text = "Do you really want to delete campaign:\n\n"
        text += f"*Title*: `{campaign.title}`\n"
        text += f"*Market*: [{campaign.market.title}]({campaign.market.url})\n"
        text += f"*Items number*: `{campaign.campaign_items.count()}`\n"
        buttons = [
            [
                KeyboardButton.a(text="Yes"),
                KeyboardButton.a(text="No"),
            ]
        ]
        bot.sendMessage(
            chat_id,
            text,
            parse_mode=bot.PARSE_MODE_MARKDOWN,
            reply_markup=ReplyKeyboardMarkup.a(
                keyboard=buttons,
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
            disable_web_page_preview=True,  # disable link preview
        )

        # change state
        state.set_name(DeleteCampaignState.CONFIRMATION.value)


@processor(
    state_manager,
    from_states=DeleteCampaignState.CONFIRMATION.value,
    success="",  # like Reset, but Reset should be handled additionally
    fail=state_types.Keep,
    message_types=message_types.Text,
)
def handle_delete_campaign_confirmation(bot: TelegramBot, update, state):
    # get data
    chat_id = update.get_chat().get_id()
    text = update.get_message().get_text()

    # send response
    if text.lower() == "yes":
        # delete campaign
        campaign_id = state.get_memory().get("campaign_id")
        campaign = Campaign.objects.filter(id=campaign_id).first()
        if not campaign:
            text = "Selected campaign didn't exist, please try to delete later"
            bot.sendMessage(chat_id, text)
            raise ProcessFailure
        campaign.delete()

        # send response
        response = "Campaign was deleted"
        bot.sendMessage(
            chat_id,
            response,
            parse_mode=bot.PARSE_MODE_MARKDOWN,
            reply_markup=remove_keyboard_markup(),
        )

    elif text.lower() == "no":
        response = "Great, no campaign was deleted"
        bot.sendMessage(
            chat_id,
            response,
            parse_mode=bot.PARSE_MODE_MARKDOWN,
            reply_markup=remove_keyboard_markup(),
        )

    else:
        response = "Use keyboard below please"
        bot.sendMessage(chat_id, response)
        raise ProcessFailure

    # reset memory
    state.reset_memory()


@processor(
    state_manager,
    from_states=DeleteCampaignState.CALLBACK.value,
    success=state_types.Keep,
    exclude_update_types=[update_types.CallbackQuery],
)
def callback_only(bot, update, state):
    text = "Please use buttons in message"
    bot.sendMessage(update.get_chat().get_id(), text)
