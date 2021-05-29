import logging

from django.utils import timezone
from checksho_bot.models import TelegramUser

from .models import User


def link_telegram_user_to_user(user: User, telegram_response: dict):
    """
    After login via telegram on client, callback with telegram data is sent
    Get or create TelegramUser and link it with User (set to User.telegram_user field)
    Transfer campaigns from TelegramUser's to User
    Set TelegramUser's user is_active=False
    """
    telegram_user = handle_telegram_user(telegram_response)
    if not telegram_user:
        logging.warning(
            "Unable to get or create telegram user on telegram login callback"
        )
        return

    telegram_user_user = getattr(telegram_user, "user", None)
    if telegram_user_user:
        transfer_campaigns_from_user_to_user(telegram_user_user, user)
        remove_user(telegram_user_user)
        remove_telegram_user_from_user(telegram_user_user)

    user.telegram_user = telegram_user
    user.save()

    return user


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


def transfer_campaigns_from_user_to_user(user_from, user_to):
    for campaign in user_from.campaigns.all():
        campaign.owner = user_to
        campaign.save()


def remove_user(user):
    user.is_active = False
    user.save()


def remove_telegram_user_from_user(user):
    """
    Since OneToOne is declared in User
    It only works when User.telegram_user = None
    TelegramUser.user = None - doesn't work
    """
    user.telegram_user = None
    user.save()



def set_user_role_on_creation(user):
    """
    If user was created by web application (not by admin panel)
    Then it is basic user and we need to set the role
    """
    if not user.role:
        user.role = User.USER
        user.save()


def create_user_for_telegram_user(telegram_user):
    """
    If user use application just from Telegram, he should have user
    so we can assign campaigns to him

    When TelegramUser will be linked with user, this created user will be deleted
    and campaigns will sync
    """
    now = timezone.now()
    username = f"{telegram_user.first_name} {now.timestamp()}"
    password = f"{username} password"

    user = User(
        username=username,
        password=password,
        role=User.USER,
        telegram_user=telegram_user,
    )
    user.save()
