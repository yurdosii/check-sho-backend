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
