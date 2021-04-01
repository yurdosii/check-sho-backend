import logging

from templates.emails import CAMPAIGN_TEMPLATE, CAMPAIGN_ITEM_TEMPLATE
from utils.parsers import *  # noqa: F401, F403
from utils.emails import send_email_message


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
    campaign_results = list(map(lambda item: parser.parse(item.url), campaign_items))
    return campaign_results


# # TODO - think about it
# def run_email_campaign(campaign):
#     pass


# # TODO - think about it
# def run_telegram_campaign(campaign):
#     pass
