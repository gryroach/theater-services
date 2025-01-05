import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from users.managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    login = models.CharField(verbose_name="login", max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="user_set",
        related_query_name="user",
        blank=True,
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="user_set",
        related_query_name="user",
        blank=True,
        verbose_name="user permissions",
    )

    USERNAME_FIELD = "login"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
    ]

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.login} {self.id}"

    def has_perm(self, perm, obj=None):
        return self.is_admin or self.is_moderator

    def has_module_perms(self, app_label):
        return self.is_admin or self.is_moderator
