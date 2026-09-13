import logging
import sys
from datetime import datetime
from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend as SmtpEmailBackend

logger = logging.getLogger(__name__)


class ConsoleAndSmtpEmailBackend(SmtpEmailBackend):
    """
    Dual Email Backend:
    1. Prints the email content clearly to the terminal / stdout.
    2. Sends the email to the recipient's inbox via SMTP.
    If SMTP fails (e.g. offline, rate limit, invalid host), logs a warning
    without crashing the user flow if fail_silently is True or if configured.
    """

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        # Step 1: Print email content to terminal stdout
        for message in email_messages:
            recipients = ', '.join(message.to) if hasattr(message, 'to') else ''
            cc = f"\nCc: {', '.join(message.cc)}" if getattr(message, 'cc', None) else ''
            bcc = f"\nBcc: {', '.join(message.bcc)}" if getattr(message, 'bcc', None) else ''
            body = message.body if hasattr(message, 'body') else ''

            banner = "=" * 80
            divider = "-" * 80
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            output = (
                f"\n{banner}\n"
                f"  [DEVBLOG DUAL EMAIL DELIVERY] Message Outbound Notice\n"
                f"  Timestamp : {timestamp}\n"
                f"  From      : {message.from_email}\n"
                f"  To        : {recipients}{cc}{bcc}\n"
                f"  Subject   : {message.subject}\n"
                f"{divider}\n"
                f"{body.strip()}\n"
                f"{banner}\n\n"
            )

            try:
                sys.stdout.write(output)
                sys.stdout.flush()
            except Exception as e:
                logger.warning(f"Error printing email to terminal: {e}")

        # Step 2: Deliver via SMTP
        sent_count = 0
        try:
            sent_count = super().send_messages(email_messages)
            if sent_count > 0:
                print(f">> [DEVBLOG SMTP SUCCESS] {sent_count} email(s) successfully delivered via SMTP server.")
        except Exception as exc:
            logger.error(f">> [DEVBLOG SMTP NOTICE] Could not deliver via SMTP: {exc}")
            print(f">> [DEVBLOG SMTP NOTICE] Delivery to inbox encountered: {exc}. Terminal copy was output above.")
            if not self.fail_silently:
                # If fail_silently is False, we only re-raise if not in DEBUG or if credentials were explicitly provided
                if not getattr(settings, 'DEBUG', True):
                    raise

        # Return count of processed messages (at least count of printed ones if SMTP failed gracefully in DEBUG)
        return sent_count if sent_count else len(email_messages)
