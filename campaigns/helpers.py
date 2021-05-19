import logging

from templates.emails import CAMPAIGN_ITEM_TEMPLATE, CAMPAIGN_TEMPLATE
from utils.emails import send_email_message
from utils.parsers import *  # noqa: F401, F403


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

    campaign = Campaign(title=title, market=market, interval=interval, is_active=True)
    campaign.save()

    for item in items:
        url = item.get("url")
        title = item.get("title")
        campaign_item = CampaignItem(
            campaign=campaign, url=url, title=title, is_active=True
        )
        campaign_item.save()
    return campaign


# # TODO - think about it
# def run_email_campaign(campaign):
#     pass


# # TODO - think about it
# def run_telegram_campaign(campaign):
#     pass
