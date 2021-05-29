import logging
from datetime import datetime
from django.utils import timezone

from templates.emails import CAMPAIGN_ITEM_TEMPLATE, CAMPAIGN_TEMPLATE
from utils.emails import send_email_message
from utils.parsers import *  # noqa: F401, F403
from utils.telegram import EMOJI


def get_market_parser(market):
    parser_name = market.title + "Parser"
    try:
        parser_class = eval(parser_name)
        return parser_class()
    except Exception:
        logging.warning(
            f"Parser with name '{parser_name}' doesn't exist for market "
            f"with title '{market.title}'"
        )
        return None


def run_endpoint_campaign(campaign):
    # TODO - will check what options are on (email / telegram / ... і від цього вже буде пригати)
    logging.info(f"Running endpoint campaign '{campaign}'")

    campaign_results = get_campaign_results(campaign)
    results = list(map(lambda result: result.to_dict(), campaign_results))
    return results


def run_email_campaign(campaign):
    logging.info(f"Running email campaign '{campaign}'")

    campaign_results = get_campaign_results(campaign)

    subject = f"Campaign {campaign.title}"
    to = [campaign.owner.email]
    body = CAMPAIGN_TEMPLATE.format(
        campaign_title=campaign.title,
        market_title=campaign.market.title,
        owner_email=campaign.owner.email,
    )

    for item in campaign_results:
        html_data = dict(
            url=item.url,
            price=item.price,
            currency=item.currency,
            before_price="",
            before_price_currency="",
            is_available="Yes" if item.is_available else "No",
        )
        if item.is_on_sale:
            html_data.update(
                dict(
                    before_price=item.before_price,
                    before_price_currency=item.currency,
                )
            )

        item_html = CAMPAIGN_ITEM_TEMPLATE.format(**html_data)

        body += item_html

    send_email_message(subject=subject, body=body, to=to)

    results = list(map(lambda result: result.to_dict(), campaign_results))
    return results


def get_campaign_item_title(market, url: str):
    if not market or not market.parser:
        return ""

    parser = market.parser
    item_result = parser.parse(url).to_dict()
    item_title = item_result.get("title")
    return item_title


def get_campaign_results(campaign):
    market = campaign.market
    if not market or not market.parser:
        return []

    parser = market.parser
    campaign_items = campaign.campaign_items.filter(is_active=True)

    campaign_results = []
    for item in campaign_items:
        item_result = parser.parse(item.url).to_dict()
        item_result["item_title"] = item.title
        campaign_results.append(item_result)
    return campaign_results


def create_campaign_from_telegram(data: str, owner=None):
    from campaigns.models import Campaign, CampaignItem, Market

    # TODO - add owner
    market_title = data.get("market_title")
    market = Market.objects.get(title=market_title)

    title = data.get("title")
    interval = data.get("interval")
    items = data.get("items")

    campaign = Campaign(
        title=title,
        market=market,
        interval=interval,
        is_active=True,
        is_telegram_campaign=True,
        owner=owner,
    )
    campaign.save()

    for item in items:
        url = item.get("url")
        title = item.get("title")
        campaign_item = CampaignItem(
            campaign=campaign, url=url, title=title, is_active=True
        )
        campaign_item.save()
    return campaign


def get_telegram_run_campaign_text(campaign, results, set_runtime=True):
    # format text by campaign
    text = f"*Campaign* '`{campaign.title}`':\n"
    text += f"*Market*: [{campaign.market.title}]({campaign.market.url})\n"

    if set_runtime:
        now_formatted = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        text += f"*Run time*: {now_formatted}\n"

    text += "\n"
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

        text += "\n"

    return text


def get_telegram_get_campaign_text(campaign):
    items = campaign.campaign_items.all()

    # format text by campaign
    text = f"*Campaign* '`{campaign.title}`':\n"
    text += f"*Market*: [{campaign.market.title}]({campaign.market.url})\n"

    if campaign.interval:
        text += f"*Interval*: `Every {campaign.interval.lower()}`\n"
    else:
        text += "*Interval*: `Not set`\n"

    text += f"*Active*: {EMOJI[campaign.is_active]}\n"
    text += f"*Type*: `{campaign.campaign_type}`\n"

    text += "\n"

    if items:
        text += "*Items*:\n\n"
    else:
        text += "*Items*: Not set\n\n"

    # format text by items
    for item in items:
        text += f"_URL_: [{item.title}]({item.url})\n"
        text += f"_Active_: {EMOJI[item.is_active]}\n"
        # TODO - handle types

        text += "\n"

    return text


def check_item_title_on_creation(item):
    """
    CampaignItem can be created with blank title, parse it from page then
    """
    if item.campaign and not item.title:
        item_title = get_campaign_item_title(item.campaign.market, item.url)
        item.title = item_title
        item.save()


def update_campaign_next_run(campaign):
    """
    If next_run is not set but campaign is active - set it
    """
    from .models import CampaignIntervalTimedelta

    if campaign.interval:
        now = timezone.now()
        interval_timedelta = CampaignIntervalTimedelta[campaign.interval].value
        next_run = interval_timedelta + now

        campaign.next_run = next_run
        campaign.save()
