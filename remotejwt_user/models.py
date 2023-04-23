from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

from typing import List


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    # You can optionally serialize managers into migrations and have them
    # available in RunPython operations. This is done by defining a
    # use_in_migrations attribute on the manager class:
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")

        # what is normalizing_email
        # For email addresses, foo@bar.com and foo@BAR.com are equivalent;
        # the domain part is case-insensitive according to the RFC specs.
        # Normalizing means providing a canonical representation,
        # so that any two equivalent email strings normalize to the same thing.
        # The comments on the Django method explain:
        # Normalize the email address by lowercasing the domain part of it.

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        # What is self.model() in django custom UserManager

        # Well what you define here is a UserManager class. This inherits from
        # the BaseUserManager class. This is a subclass of the Manager class.
        # You actually use manager all the time. For example SomeModel.objects
        # is a manager.

        # A manager has, if it is used, a reference to the model it manages.
        # So SomeModel.objects is a manager, but that manager has an attribute
        # .model that actually refers back to the SomeModel class.

        # In this case your self.model will refer to User model

        # Sets the user’s password to the given raw string, taking care of the password hashing.
        # Doesn’t save the User object.
        user.set_password(password)
        user.save(using=self._db)
        return user

        # Q: using model.save() from django shell will not validate the data

        # Creating an instance of a Model and calling save on that instance
        # does not call full_clean. Therefore it’s possible for invalid data
        # to enter your database if you don’t manually call the full_clean
        # function before saving.

        # Object managers’ default create function also doesn’t call full_clean.

        # But in general, it's not good practice to add validation in the
        # save() method. The reason is that in most Django apps, you'd create
        # a form (a ModelForm) which would call the validation methods and be
        # able to return something meaningful to the user when validation
        # fails.

        # When the model's save() method is called it's too late to show
        # something to the user, so you can only raise an exception at that
        # point (and crash).

        # The normal procedure (which the admin forms use) is: validate the
        # form by calling form.is_valid() (which calls full_clean() on the
        # model), then if and only if the form is valid, save the model.

        # The shell is not the regular interaction method and should be used
        # only very carefully as it bypasses the normal flow of the
        # application.

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        # What setdefault function does is that while creating a user if the
        # calling function  is not providing any values then set is_staff and
        # is_superuser both to False for this user.
        # we want to save the email as lower.
        return self._create_user(email.lower(), password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""

        # For superuser to login to admin the following three conditions should
        # be satisfied

        # is_staff  => True  (if exit).
        # is_active  => True .
        # is_superuser => True.

        # Set the values if they are not defined
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        # Option1: (Change the values internally irrespective of the user input)

        # We want for super user is_staff, is_superuser and is_active to be
        # true. So the below will change the value to True even if someone
        # passes False to any value. But this approach is not good since the
        # user will not know that his values are getting manupulated.

        # extra_fields['is_staff'] = True
        # extra_fields['is_superuser'] = True
        # extra_fields['is_active'] = True

        # Option2:

        # Check the values provided, if not True raise exception
        # The below approach is preferred so that the end user knows that he supplied wrong data.

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_active") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        # what is need for setdefault and again raise error

        # setdefault sets the value only if the key is not already present in the dict.
        # The caller of the function could still pass extra_fields with some values of id_staff
        # or is_superuser.

        # What this function does is that while creating a superuser if the calling function
        # is not providing any values then set is_staff and is_superuser both to True for this user.

        # But, if the values are provided then check if those are True and
        # raise exceptions otherwise.

        # we want to save the email as lower.
        return self._create_user(email.lower(), password, **extra_fields)


class User(AbstractUser):
    objects = UserManager()  # type: ignore

    """User model."""

    # We are inheriting AbstractUser and username is already defined there
    # We dont want to use username as we will be using email as login
    # inorder to not use username we say username = None
    username = None  # type: ignore
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    location = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    # We are inheriting AbstractUser and email is already defined there
    # its defined as blank=TRUE in the AbstractUser.
    # But we will be using it as the login field so also want to be unique
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
    # This creates a per user based unique id or nounce
    jwt_secret = models.UUIDField(editable=False, default=uuid.uuid4)

    # A string describing the name of the field on the user model that is
    # used as the unique identifier. This will usually be a username of
    # some kind, but it can also be an email address, or any other unique
    # identifier. The field must be unique (i.e., have unique=True set in its
    # definition), unless you use a custom authentication backend that can
    # support non-unique usernames.
    USERNAME_FIELD = "email"

    # REQUIRED_FIELDS DEFINITION
    # A list of the field names that will be prompted for when creating a user
    # via the createsuperuser management command. The user will be prompted to
    # supply a value for each of these fields. It must include any field for which
    # blank is False or undefined and may include additional fields you want prompted
    # for when a user is created interactively. REQUIRED_FIELDS has no effect in other
    # parts of Django, like creating a user in the admin.

    # presently we dont want to be asked for anything while createsuperuser
    REQUIRED_FIELDS: List = []

    # /lib/python3.9/site-packages/django/contrib/auth/models.py  does this
    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"
        db_table = "user"

    def __str__(self):
        return self.email
