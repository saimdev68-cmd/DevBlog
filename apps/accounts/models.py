from datetime import timedelta
import secrets
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier for auth."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with email authentication."""

    email = models.EmailField(_("email address"), unique=True, db_index=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Designates whether this user should be treated as active."),
    )
    is_email_verified = models.BooleanField(
        _("email verified"),
        default=False,
        help_text=_("Designates whether this user has verified their email address with OTP."),
    )
    is_google_user = models.BooleanField(
        _("google account"),
        default=False,
        help_text=_("Designates whether this user authenticated with Google OAuth."),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full if full else self.email

    @property
    def is_google_account(self):
        return self.is_google_user or not self.has_usable_password()


class Profile(models.Model):
    """Author profile for biography, avatar, and social presence."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(_("bio"), max_length=500, blank=True)
    website = models.URLField(_("website"), max_length=200, blank=True)
    github = models.URLField(_("GitHub"), max_length=200, blank=True)
    linkedin = models.URLField(_("LinkedIn"), max_length=200, blank=True)
    twitter = models.URLField(_("X / Twitter"), max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("profile")
        verbose_name_plural = _("profiles")

    def __str__(self):
        return f"{self.user.email}'s profile"

    @property
    def display_name(self):
        return self.user.full_name


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()


class EmailVerificationOTP(models.Model):
    """Stores 6-digit One-Time Passwords for user email verification."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_otps',
    )
    new_email = models.EmailField(_("new email address"), blank=True, null=True)
    otp_code = models.CharField(_("OTP code"), max_length=6)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    expires_at = models.DateTimeField(_("expires at"))
    is_used = models.BooleanField(_("is used"), default=False)
    attempts = models.PositiveIntegerField(_("attempts"), default=0)

    class Meta:
        verbose_name = _("email verification OTP")
        verbose_name_plural = _("email verification OTPs")
        ordering = ['-created_at']

    def __str__(self):
        target = self.new_email or self.user.email
        return f"OTP {self.otp_code} for {target} (used={self.is_used}, expired={self.is_expired})"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired

    @classmethod
    def generate_otp_for_user(cls, user, new_email=None, validity_minutes=10, send_email=True):
        """
        Invalidates existing active OTPs for user (and specific new_email if applicable),
        creates a new cryptographically secure 6-digit code, and triggers the email notification.
        """
        if new_email:
            cls.objects.filter(user=user, new_email__iexact=new_email, is_used=False).update(is_used=True)
        else:
            cls.objects.filter(user=user, new_email__isnull=True, is_used=False).update(is_used=True)

        code = f"{secrets.randbelow(900000) + 100000:06d}"
        expires_at = timezone.now() + timedelta(minutes=validity_minutes)

        otp = cls.objects.create(
            user=user,
            new_email=new_email,
            otp_code=code,
            expires_at=expires_at,
        )

        if send_email:
            if new_email:
                from .emails import send_email_change_otp
                send_email_change_otp(user, new_email, code)
            else:
                from .emails import send_otp_verification_email
                send_otp_verification_email(user, code)

        return otp


