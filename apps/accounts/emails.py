import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger('apps.accounts')


def send_otp_verification_email(user, otp_code):
    """
    Sends a branded 6-digit OTP verification email to the user.
    In development (DEBUG=True), this is routed to the terminal stdout via console.EmailBackend.
    """
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
        # Fallback plaintext message if template rendering fails
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
        logger.info(f"Verification OTP email sent to {user.email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send verification OTP email to {user.email}: {exc}")
        return False


def send_email_change_otp(user, new_email, otp_code):
    """
    Sends an OTP verification code to the requested *new* email address.
    In development (DEBUG=True), this is printed directly to terminal stdout.
    """
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
        logger.info(f"Email change OTP sent to {new_email} for user {user.email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send email change OTP to {new_email}: {exc}")
        return False

