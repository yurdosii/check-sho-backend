from django.core.paginator import Paginator
from django_tgbot.types.inlinekeyboardbutton import InlineKeyboardButton
from django_tgbot.types.replykeyboardremove import ReplyKeyboardRemove

from campaigns.models import Campaign


def remove_keyboard_markup():
    return ReplyKeyboardRemove.a(remove_keyboard=True)


def get_paginator_pages(page, max_pages):
    previous_page = page - 1 if page - 1 > 0 else max_pages
    next_page = (page + 1) if page + 1 <= max_pages else 1
    return (previous_page, next_page)


def get_paginator_and_pages(page: int, per_page: int = 5, order_by=None):
    # TODO - campaigns by user
    # TODO - cache somehow this

    if order_by:
        campaigns = Campaign.objects.all().order_by(order_by)
    else:
        campaigns = Campaign.objects.all()

    p = Paginator(campaigns, per_page)

    previous_page, next_page = get_paginator_pages(page, p.num_pages)

    return p, previous_page, next_page


def get_navigation_buttons(
    page: int, previous_page: int, next_page: int, max_pages: int
):
    navigation_buttons = [
        InlineKeyboardButton.a("❮", callback_data=f"#{previous_page}"),
        InlineKeyboardButton.a(f"{page}/{max_pages}", callback_data=f"#{page}"),
        InlineKeyboardButton.a("❱", callback_data=f"#{next_page}"),
    ]
    return navigation_buttons
