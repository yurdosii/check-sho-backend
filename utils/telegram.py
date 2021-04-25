import functools
import logging


EMOJI = {
    "YES": "✅",
    "NO": "❌",
}


def telegram_command(func):
    @functools.wraps(func)
    def wrapper_telegram_command(*args, **kwargs):
        logging.info(f"Running telegram command: /{func.__name__}")
        result = func(*args, **kwargs)
        return result

    return wrapper_telegram_command


# Notes:
# - '*' - bold в боті
# - '**' - bold в телезі для юзера
# - '_' - italic в боті
# - '__' - italic в телезі для юзера
