import jwt
from django.db import models
from django.contrib.auth.models import (AbstractUser, BaseUserManager)
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timedelta
from utils.models import BaseAbstractModel
from utils.managers import CustomQuerySet
from django.conf import settings
from fernet_fields import EncryptedTextField


class UserManager(BaseUserManager):
    """
    We need to override the `create_user` method so that users can
    only be created when all non-nullable fields are populated.
    """

    def create_user(
            self,
            first_name=None,
            last_name=None,
            email=None,
            password=None,
            role='CL'
    ):
        """
        Create and return a `User` with an email, first name, last name and
        password.
        """

        if not first_name:
            raise TypeError('Hello, Kindly provide us with your First Name.')

        if not last_name:
            raise TypeError('Hello, Kindly provide us with your Last Name.')

        if not email:
            raise TypeError(
                'Hello, Kindly provide us with your Email Address.')

        if not password:
            raise TypeError(
                'Hello, Kindly provide us with a Password to Secure your account')

        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=self.normalize_email(email),
            username=self.normalize_email(email))
        user.set_password(password)
        user.role = role
        user.save()
        return user

    def create_superuser(
            self,
            first_name=None,
            last_name=None,
            email=None,
            password=None
    ):
        """Create a `User` who is also a superuser"""
        if not first_name:
            raise TypeError('Hello, Kindly provide us with your First Name.')

        if not last_name:
            raise TypeError('Hello, Kindly provide us with your Last Name.')

        if not email:
            raise TypeError(
                'Hello, Kindly provide us with your Email Address.')

        if not password:
            raise TypeError(
                'Hello, Kindly provide us with a Password to Secure your account')

        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=self.normalize_email(email),
            role='AA')
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.is_verified = True
        user.set_password(password)
        user.save()


class User(AbstractUser, BaseAbstractModel):
    """This class defines the User model"""

    USER_ROLES = (
        ('AA', 'ACRES ADMIN'),
        ('CA', 'CLIENT ADMIN'),
        ('CL', 'CLIENT'),
    )

    username = models.CharField(
        null=True, blank=True, max_length=100, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(
        verbose_name='user role', max_length=2, choices=USER_ROLES, default='CL')
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()
    active_objects = CustomQuerySet.as_manager()

    def __str__(self):
        return f'{self.email}'

    @property
    def get_email(self):
        """
        This method is required by Django for things like handling emails.
        Typically, this would be the user's first and last name. Since we do
        not store the user's real name, we return their emails instead.
        """
        return self.email

    @property
    def token(self):
        """
        We need to make the method for creating our token private. At the
        same time, it's more convenient for us to access our token with
        `user.token` and so we make the token a dynamic property by wrapping
        in in the `@property` decorator.
        """
        return self._generate_jwt_token()

    def _generate_jwt_token(self):
        """
        We generate JWT token and add the user id, username and expiration
        as an integer.
        """
        token_expiry = datetime.now() + timedelta(hours=24)

        token = jwt.encode({
            'id': self.pk,
            'email': self.get_email,
            'exp': int(token_expiry.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')

        return token.decode('utf-8')


class BlackList(BaseAbstractModel):
    """
    This class defines black list model.
    Tokens of logged out users are stored here.
    """

    token = models.CharField(max_length=200, unique=True)

    @staticmethod
    def delete_tokens_older_than_a_day():
        """
        This method deletes tokens older than one day
        """
        past_24 = datetime.now() - timedelta(hours=24)

        BlackList.objects.filter(created_at__lt=past_24).delete()


class UserProfile(BaseAbstractModel):
    """This class defines a Profile model for all Users"""

    QUESTION_CHOICES = (
        ('What is the name of your favorite teacher?',
         'What is the name of your favorite teacher?'),
        ('What is the name of your favorite month?',
         'What is the name of your favorite month?'),
        ('What is the name of your favorite sport?',
         'What is the name of your favorite sport?'),
        ('What is the name of your favorite music instrument?',
         'What is the name of your favorite music instrument?'),
        ('What was your childhood nickname?',
         'What was your childhood nickname?'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=16, null=True, blank=False)
    address = JSONField(verbose_name='physical address',
                        encoder=DjangoJSONEncoder, default=dict)
    image = models.URLField(null=True, blank=True)
    security_question = models.CharField(
        max_length=255, null=True, blank=False, choices=QUESTION_CHOICES)
    security_answer = EncryptedTextField(null=True)
    employer = models.CharField(max_length=255, null=True, blank=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    next_of_kin = models.CharField(max_length=255, blank=True, null=True)
    next_of_kin_contact = models.CharField(
        max_length=17, blank=True, null=True)
    bio = models.TextField(blank=True, max_length=255)

    objects = models.Manager()
    active_objects = CustomQuerySet.as_manager()

    def __str__(self):
        return f'{self.user}\'s Profile'


class Client(BaseAbstractModel):
    """This class defines the client Company Model"""

    APPROVAL_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revoked', 'Revoked'),
    ]

    approval_status = models.CharField(
        max_length=10, choices=APPROVAL_STATUS, default='pending')
    client_name = models.CharField(max_length=100, unique=True)
    client_admin = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='employer')
    phone = models.CharField(max_length=17, unique=True)
    email = models.EmailField(unique=True)
    address = JSONField(verbose_name='physical address',
                        encoder=DjangoJSONEncoder)
    objects = models.Manager()
    active_objects = CustomQuerySet.as_manager()

    def __str__(self):
        return self.client_name


class PasswordResetToken(models.Model):
    """This class creates a Password Reset Token model."""

    token = models.CharField(max_length=400)
    created = models.DateTimeField(auto_now=True)
    is_valid = models.BooleanField(default=True)


class ClientReview(BaseAbstractModel):
    """This class defines the model for the client reviews"""

    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviewer')
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name='reviewed_client')
    review = models.TextField()

    objects = models.Manager()
    active_objects = CustomQuerySet.as_manager()

    def __str__(self):
        return f'Review by {self.reviewer} on {self.created_at}'


class ReplyReview(BaseAbstractModel):
    """This class defines the model for the replies to the client's reviews"""

    review = models.ForeignKey(
        ClientReview, on_delete=models.CASCADE, related_name='replies')
    reply = models.TextField()
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reply')

    objects = models.Manager()
    active_objects = CustomQuerySet.as_manager()

    def __str__(self):
        return f'Review by {self.reviewer} on {self.created_at}'
