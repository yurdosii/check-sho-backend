from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ADMIN = "ADMIN"
    USER = "USER"
    CUSTOM_ROLE_CHOICES = (
        (ADMIN, "ADMIN"),
        (USER, "USER"),
    )
    role = models.CharField(max_length=20, choices=CUSTOM_ROLE_CHOICES, db_index=True)

    def __str__(self):
        return self.username
