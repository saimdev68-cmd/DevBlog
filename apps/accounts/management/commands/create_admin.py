import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Safely and idempotently create the initial production superuser from environment variables."

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '').strip()
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '').strip()
        first_name = os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', 'Admin').strip()
        last_name = os.environ.get('DJANGO_SUPERUSER_LAST_NAME', 'User').strip()

        # Validate required environment variables
        if not email or not password:
            self.stderr.write(
                self.style.ERROR(
                    "Error: DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD environment variables are required."
                )
            )
            return

        User = get_user_model()
        normalized_email = User.objects.normalize_email(email)

        # Idempotency check: verify if the user already exists
        if User.objects.filter(email=normalized_email).exists():
            existing_user = User.objects.get(email=normalized_email)
            if existing_user.is_superuser:
                self.stdout.write(
                    self.style.SUCCESS(f"Admin user already exists: {normalized_email}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"User with email {normalized_email} already exists but is not a superuser. Existing account was not modified."
                    )
                )
        else:
            # Create the superuser using project's existing CustomUserManager
            try:
                User.objects.create_superuser(
                    email=normalized_email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Superuser created successfully: {normalized_email}")
                )
            except Exception as exc:
                raise CommandError(f"Failed to create superuser: {exc}")

        # Ensure published articles with generated banner images exist
        try:
            from django.core.management import call_command
            call_command('seed_data')
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"Note: seed_data skipped: {exc}"))

