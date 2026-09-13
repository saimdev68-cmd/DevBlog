import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_otp_verification_email_task(self, user_id, otp_code):
    """
    Celery background task to render and send the 6-digit OTP verification email.
    Uses configured EMAIL_BACKEND (which prints to terminal and sends via SMTP).
    """
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error(f"[Celery] User with id {user_id} not found. Aborting OTP email.")
        return False

    subject = f"[DevBlog] Your Verification Code: {otp_code}"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'DevBlog <noreply@devblog.com>')
    to_email = [user.email]

    context = {
        'user': user,
        'otp_code': otp_code,
        'validity_minutes': 10,
        'site_name': 'DevBlog',
    }

    try:
        html_content = render_to_string('accounts/emails/otp_verification_email.html', context)
        text_content = render_to_string('accounts/emails/otp_verification_email.txt', context)
    except Exception:
        text_content = (
            f"Hello {user.first_name or 'there'},\n\n"
            f"Your DevBlog verification code is: {otp_code}\n\n"
            f"This code is valid for 10 minutes. Please do not share it with anyone.\n\n"
            f"If you did not request this code, please ignore this email.\n\n"
            f"— The DevBlog Team"
        )
        html_content = None

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    if html_content:
        msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        logger.info(f"[Celery] Verification OTP email dispatched for {user.email}")
        return True
    except Exception as exc:
        logger.error(f"[Celery] Error delivering OTP email to {user.email}: {exc}")
        try:
            self.retry(exc=exc)
        except Exception:
            return False


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_email_change_otp_task(self, user_id, new_email, otp_code):
    """
    Celery background task to render and send the email change OTP confirmation.
    """
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error(f"[Celery] User with id {user_id} not found. Aborting email change OTP.")
        return False

    subject = f"[DevBlog] Confirm Your New Email Address: {otp_code}"
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'DevBlog <noreply@devblog.com>')
    to_email = [new_email]

    context = {
        'user': user,
        'new_email': new_email,
        'otp_code': otp_code,
        'validity_minutes': 10,
        'site_name': 'DevBlog',
    }

    text_content = (
        f"Hello {user.first_name or 'Reader'},\n\n"
        f"You requested to change your DevBlog account email address to: {new_email}\n\n"
        f"Your 6-digit confirmation code is: {otp_code}\n\n"
        f"This code will expire in 10 minutes. If you did not request this change, please contact support immediately.\n\n"
        f"— The DevBlog Team"
    )

    try:
        html_content = render_to_string('accounts/emails/otp_verification_email.html', context)
    except Exception:
        html_content = None

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    if html_content:
        msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        logger.info(f"[Celery] Email change OTP email dispatched for {new_email}")
        return True
    except Exception as exc:
        logger.error(f"[Celery] Error delivering email change OTP to {new_email}: {exc}")
        try:
            self.retry(exc=exc)
        except Exception:
            return False


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def send_generic_email_task(self, subject, text_content, from_email=None, recipient_list=None, html_content=None):
    """
    General purpose background email delivery task for Celery.
    """
    if not recipient_list:
        return False

    from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'DevBlog <noreply@devblog.com>')
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    if html_content:
        msg.attach_alternative(html_content, "text/html")

    try:
        msg.send(fail_silently=False)
        return True
    except Exception as exc:
        logger.error(f"[Celery] Error in generic email task: {exc}")
        try:
            self.retry(exc=exc)
        except Exception:
            return False
