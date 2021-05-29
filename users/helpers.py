import logging

from checksho_bot.models import TelegramUser

from .models import User


def handle_telegram_user(data: dict):
    telegram_id = data.get("id")
    first_name = data.get("first_name")
    if not telegram_id or not first_name:
        logging.warning("Wrong telegram response")
        return

    telegram_user, _ = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            "first_name": first_name,
            "username": data.get("username"),
            "is_bot": False,
        },
    )
    return telegram_user


def link_telegram_user_to_user(user: User, telegram_response: dict):
    """
    After login via telegram on client callback with telegram data is sent
    Get or create TelegramUser and link it with User (set to User.telegram_user field)
    """
    telegram_user = handle_telegram_user(telegram_response)
    if not telegram_user:
        logging.warning(
            "Unable to get or create telegram user on telegram login callback"
        )
        return

    if not user.telegram_user:
        # TODO - telegram_user should be FK, not OneToOne
        user.telegram_user = telegram_user
        user.save()

    return user
