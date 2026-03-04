from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

from typing import List


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        return self._create_user(email.lower(), password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_active") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email.lower(), password, **extra_fields)


class User(AbstractUser):
    """User model."""

    objects = UserManager()

    username = None
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    location = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(
        _("email address"),
        help_text="Please Enter valid Email Address",
        unique=True,
        error_messages={
            "unique": _("This email already exists."),
        },
    )
    modified_date = models.DateTimeField(_("modified date"), auto_now=True)
    creation_date = models.DateTimeField(_("creation date"), auto_now_add=True)
    jwt_secret = models.UUIDField(editable=False, default=uuid.uuid4)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: List[str] = []

    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"
        db_table = "user"

    def __str__(self):
        return self.email
