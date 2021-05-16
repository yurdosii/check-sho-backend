from django_tgbot.types.replykeyboardremove import ReplyKeyboardRemove


def remove_keyboard_markup():
    return ReplyKeyboardRemove.a(remove_keyboard=True)
