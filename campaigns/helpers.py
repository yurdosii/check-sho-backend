import logging
from datetime import datetime

from django.conf import settings
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
        item_result["item_is_notify_sale"] = item.is_notify_sale
        item_result["item_is_notify_available"] = item.is_notify_available
        campaign_results.append(item_result)
    return campaign_results


def create_campaign_from_telegram(data: str, owner=None):
    from campaigns.models import Campaign, CampaignItem, Market

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
        # get result data
        result_item_title = result["item_title"]
        result_item_is_notify_sale = result["item_is_notify_sale"]
        result_item_is_notify_available = result["item_is_notify_available"]
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
        text += f"_Available_: {EMOJI[result_is_available]}"
        if not result_is_available:
            text += "\n\n"
            continue

        # handle notify availability
        if result_item_is_notify_available:
            text += "   *(!!!)*"

        # set new line for available
        text += "\n"

        # handle price and sale
        text += f"_Price_: `{result['price']}`\n"
        text += f"_On sale_: {EMOJI[result_is_on_sale]}\n"

        if result_is_on_sale:
            diff = round(result_price_before - result_price, 2)
            text += f"_Price before_: `{result_price_before}` (-*{diff}*)"

            # handle notify sale
            if result_item_is_notify_sale:
                text += "   *(!!!)*"

            # set new line for on sale
            text += "\n"

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

        if item.is_notify_sale or item.is_notify_available:
            notify = ", ".join(item.notify_list)
            text += f"_Notify_: `{notify}`\n"

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


def set_campaign_next_run(campaign):
    """
    If next_run is not set but campaign is active - set it
    """
    if campaign.interval:
        now = timezone.now()
        next_run = now + campaign.interval_timedelta

        campaign.next_run = next_run
        campaign.save()


def unset_campaign_next_run(campaign):
    """
    If next_run is set but campaign isn't active - unset it
    """
    campaign.next_run = None
    campaign.save()


def run_campaign(user, campaign):
    """
    Get campaign results
    Send them to Telegram and/or email
    Return notification message for client
    """
    logging.info(f"Running '{campaign.title}' campaign")
    campaign_results = get_campaign_results(campaign)

    sent_to = []

    # send to telegram
    telegram_user = user.telegram_user
    if campaign.is_telegram_campaign and telegram_user:
        send_campaign_results_to_telegram(campaign, telegram_user, campaign_results)

        sent_to.append("Telegram")

    # send to email
    if campaign.is_email_campaign and campaign.owner and campaign.owner.email:
        if getattr(settings, "EMAIL_HOST", None):
            send_campaign_results_to_email(campaign, campaign_results)
            sent_to.append("email")
        else:
            logging.warning("Email configuration is missing")

    # update last_run and next_run
    update_campaign_run_info_after_run(campaign)

    # create notification message
    result = "Campaign was run. Please check your " + " and ".join(sent_to)

    return result


def send_campaign_results_to_telegram(campaign, telegram_user, results):
    """
    Having campaign run results, send them to Telegram
    """
    from checksho_bot.bot import bot

    logging.info(f"Send results to Telegram of '{campaign.title}' campaign")

    # get telegram chat
    telegram_chat = telegram_user.user_telegram_chat
    if not telegram_chat:
        logging.warning(
            f"No telegram chat for telegram user '{telegram_user.first_name}'"
        )
        return

    # get run campaign text
    chat_id = telegram_chat.telegram_id
    text = "Result of running campaign:\n\n"
    text += get_telegram_run_campaign_text(campaign, results)

    # send message to Telegram
    bot.sendMessage(
        chat_id,
        text,
        parse_mode=bot.PARSE_MODE_MARKDOWN,
        disable_web_page_preview=True,  # disable link preview
    )


def send_campaign_results_to_email(campaign, results):
    """
    Having campaign run results, send them to email
    """
    logging.info(f"Send results to email of '{campaign.title}' campaign")

    # prepare for email message
    subject = f"Campaign {campaign.title}"
    to = [campaign.owner.email]
    body = CAMPAIGN_TEMPLATE.format(
        campaign_title=campaign.title,
        market_title=campaign.market.title,
        market_url=campaign.market.url,
        campaign_runtime=timezone.now().strftime("%d/%m/%Y %H:%M:%S"),
    )

    body += get_email_campaign_body(results)

    # send email message
    send_email_message(subject=subject, body=body, to=to)


def get_email_campaign_body(results: list):
    body = ""
    for result in results:
        # get result data
        result_item_title = result["item_title"]
        result_item_is_notify_sale = result["item_is_notify_sale"]
        result_item_is_notify_available = result["item_is_notify_available"]
        result_url = result["url"]
        result_is_available = result["is_available"]
        result_price = result["price"]
        result_currency = result["currency"]
        result_is_on_sale = result["is_on_sale"]
        result_price_before = result["price_before"]

        is_notify_sale = (
            "  (!!!)" if result_item_is_notify_sale and result_is_on_sale else ""
        )
        is_notify_available = (
            "  (!!!)" if result_item_is_notify_available and result_is_available else ""
        )

        # prepare html data
        html_data = dict(
            url=result_url,
            title=result_item_title,
            is_available="Yes" if result_is_available else "No",
            is_on_sale="Yes" if result_is_on_sale else "No",
            price=result_price,
            currency=result_currency,
            before_price="",
            before_price_currency="",
            is_notify_sale=is_notify_sale,
            is_notify_available=is_notify_available,
        )
        if result_is_on_sale:
            html_data.update(
                dict(
                    before_price=result_price_before,
                    before_price_currency=result_currency,
                )
            )

        item_html = CAMPAIGN_ITEM_TEMPLATE.format(**html_data)

        body += item_html

    return body


def update_campaign_run_info_after_run(campaign):
    now = timezone.now()
    campaign.last_run = now
    campaign.next_run = now + campaign.interval_timedelta
    campaign.save()


def run_campaigns(user, campaigns):
    """
    Celery scheduled task will call this method to run campaigns for
    """
    telegram_campaigns_info_to_run = []
    email_campaigns_info_to_run = []
    for campaign in campaigns:
        results = get_campaign_results(campaign)

        if campaign.is_telegram_campaign:
            telegram_campaigns_info_to_run.append((campaign, results))
        if campaign.is_email_campaign:
            email_campaigns_info_to_run.append((campaign, results))

        if campaign.is_telegram_campaign or campaign.is_email_campaign:
            update_campaign_run_info_after_run(campaign)

    send_campaigns_results_to_telegram(user, telegram_campaigns_info_to_run)
    send_campaigns_results_to_email(user, email_campaigns_info_to_run)


def send_campaigns_results_to_telegram(user, results_info):
    """
    Having user and results of campaigns that should be sent to Telegram
    Send them to Telegram
    """
    telegram_user = user.telegram_user
    if not telegram_user:
        logging.warning(
            f"TelegramUser of user '{user.username}' isn't set. "
            "Unable to send results to Telegram"
        )
        return

    for result_info in results_info:
        campaign, campaign_results = result_info
        send_campaign_results_to_telegram(campaign, telegram_user, campaign_results)


def send_campaigns_results_to_email(user, results_info):
    """ "
    Having user and results of campaigns that should be sent to email
    Send them to email
    """
    if not user.email:
        logging.warning("User's email isn't set. Unable to send results to email")
        return

    if not getattr(settings, "EMAIL_HOST", None):
        logging.warning("Email configuration missing")
        return

    # prepare for email message
    subject = "CheckSho: results of scheduled campaigns"
    to = [user.email]
    body = """<h2>Results of scheduled campaigns:</h2>"""

    # get messages's body
    for result_info in results_info:
        campaign, campaign_results = result_info

        body += CAMPAIGN_TEMPLATE.format(
            campaign_title=campaign.title,
            market_title=campaign.market.title,
            market_url=campaign.market.url,
            campaign_runtime=timezone.now().strftime("%d/%m/%Y %H:%M:%S"),
        )
        body += get_email_campaign_body(campaign_results)
        body += """<br><br>"""

    # send email message
    send_email_message(subject=subject, body=body, to=to)
