from django.contrib import admin
from .models import TelegramChat, TelegramState, TelegramUser

admin.site.register([TelegramUser, TelegramChat, TelegramState])
