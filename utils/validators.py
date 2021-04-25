from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


def is_url_valid(url):
    try:
        validator = URLValidator()
        validator(url)
    except ValidationError:
        return False
    return True


def is_campaign_item_url_is_valid(url, market, items):
    if not is_url_valid(url):
        return False, "URL is invalid"

    items_urls = [item["url"] for item in items]
    if url in items_urls:
        return False, "Item with given URL already exists"

    if not market.is_url_from_market(url):
        return False, f"'{market.title}' market doesn't have given page"

    return True, ""

    # TODO - запит по сторінці і перевірку на 404 + може на чи існує продукт
