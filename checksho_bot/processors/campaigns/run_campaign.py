from datetime import datetime
from enum import Enum

from django_tgbot.decorators import processor
from django_tgbot.exceptions import ProcessFailure
from django_tgbot.state_manager import state_types, update_types
from django_tgbot.types.inlinekeyboardbutton import InlineKeyboardButton
from django_tgbot.types.inlinekeyboardmarkup import InlineKeyboardMarkup
from django_tgbot.types.update import Update

from campaigns.helpers import get_campaign_results
from campaigns.models import Campaign
from checksho_bot.bot import TelegramBot, state_manager
from checksho_bot.models import TelegramState
from utils.telegram import EMOJI, telegram_command

from ..utils import get_navigation_buttons, get_paginator_and_pages


class RunCampaignState(Enum):
    CALLBACK = "run_campaign__callback"


def get_campaigns_buttons(page: int):
    p, previous_page, next_page = get_paginator_and_pages(page)

    campaigns_by_page = p.page(page).object_list
    campaigns_buttons = list(
        map(
            lambda campaign: (
                [
                    InlineKeyboardButton.a(
                        f"{campaign.title} ({campaign.campaign_items.count()} items)",
                        callback_data=str(campaign.id),
                    )
                ]
            ),
            campaigns_by_page,
        )
    )

    navigation_buttons = get_navigation_buttons(
        page, previous_page, next_page, p.num_pages
    )
    campaigns_buttons.append(navigation_buttons)

    return campaigns_buttons


def get_run_campaign_text(campaign: Campaign, results: list):
    # get check time
    now = datetime.now()
    now_formatted = now.strftime("%d/%m/%Y %H:%M:%S")

    # format text by campaign
    text = f"*Campaign* '`{campaign.title}`':\n\n"
    text += f"*Market*: [{campaign.market.title}]({campaign.market.url})\n"
    text += f"*Run time*: {now_formatted}\n\n"
    text += "*Items*:\n\n"

    # format text by items
    for result in results:
        # TODO - check on sale (write '!!!!!!!!!!' if it is on sale for example)

        # get result data
        result_item_title = result["item_title"]
        result_url = result["url"]
        result_is_wrong_url = result["is_wrong_url"]
        result_is_available = result["is_available"]
        result_price = result["price"]
        result_is_on_sale = result["is_on_sale"]
        result_price_before = result["price_before"]

        text += f"_URL_: [{result_item_title}]({result_url})\n"

        # handle wrong url
        if result_is_wrong_url:
            text += "_Error_: something is wrong with the item "
            text += "(item can be removed, link can be invalid), "
            text += "please check it manually\n\n"
            continue

        # handle item availability
        text += f"_Available_: {EMOJI[result_is_available]}\n"
        if not result_is_available:
            text += "\n\n"
            continue

        # handle price and sale
        text += f"_Price_: `{result['price']}`\n"
        text += f"_On sale_: {EMOJI[result_is_on_sale]}\n"

        if result_is_on_sale:
            diff = result_price_before - result_price
            text += f"_Price before_: `{result_price_before}` (-*{diff}*)\n"

        text += "\n\n"

    return text


@telegram_command
def run_campaign(bot: TelegramBot, update: Update, state: TelegramState):
    # get chat data
    chat_id = update.get_chat().get_id()

    # save page
    state.update_memory({"page": 1})

    # send response
    campaigns_buttons = get_campaigns_buttons(1)
    text = "Select campaign to run:"
    bot.sendMessage(
        chat_id,
        text,
        parse_mode=bot.PARSE_MODE_MARKDOWN,
        reply_markup=InlineKeyboardMarkup.a(inline_keyboard=campaigns_buttons),
    )

    # changing state
    state.set_name(RunCampaignState.CALLBACK.value)


@processor(
    state_manager,
    from_states=RunCampaignState.CALLBACK.value,
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

        # check page
        page = int(callback_data[1:])
        if page == state.get_memory().get("page"):
            return

        # save page
        state.update_memory({"page": page})

        # send response
        campaigns_buttons = get_campaigns_buttons(page)
        bot.editMessageText(
            "Select campaign to run:",
            chat_id,
            message_id,
            parse_mode=bot.PARSE_MODE_MARKDOWN,
            reply_markup=InlineKeyboardMarkup.a(inline_keyboard=campaigns_buttons),
        )

        # change state
        state.set_name(RunCampaignState.CALLBACK.value)

    else:
        # run campaign

        # typing action
        bot.sendChatAction(chat_id, bot.CHAT_ACTION_TYPING)

        # check campaign
        campaign = Campaign.objects.filter(id=callback_data).first()
        if not campaign:
            text = "Selected campaign didn't exist, please try to run later"
            bot.sendMessage(chat_id, text)
            raise ProcessFailure

        # get results
        results = get_campaign_results(campaign)
        text = get_run_campaign_text(campaign, results)

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


@processor(
    state_manager,
    from_states=RunCampaignState.CALLBACK.value,
    success=state_types.Keep,
    exclude_update_types=[update_types.CallbackQuery],
)
def callback_only(bot, update, state):
    text = "Please use buttons in message"
    bot.sendMessage(update.get_chat().get_id(), text)
