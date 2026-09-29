"""
Custom User model.

We replace Django's default username-based user with an email-based one,
as required by the assignment (``USERNAME_FIELD = "email"``).
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password are always required by definition

    class Meta:
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email
