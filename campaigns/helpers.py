import logging

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


def get_campaign_results(campaign):
    market = campaign.market
    if not market or not market.parser:
        return []

    parser = market.parser
    campaign_items = campaign.campaign_items.filter(is_active=True)
    campaign_results = list(map(lambda item: parser.parse(item.url), campaign_items))
    return campaign_results


# TODO - think about it
def run_email_campaign(campaign):
    pass


# TODO - think about it
def run_telegram_campaign(campaign):
    pass
