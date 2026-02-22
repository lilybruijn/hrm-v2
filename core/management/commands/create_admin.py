from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = "Create admin user if not exists"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = os.environ.get("ADMIN_USERNAME")
        email = os.environ.get("ADMIN_EMAIL")
        password = os.environ.get("ADMIN_PASSWORD")

        if not username or not email or not password:
            raise CommandError("ADMIN_USERNAME, ADMIN_EMAIL or ADMIN_PASSWORD missing in environment")

        if User.objects.filter(username=username).exists():
            self.stdout.write("Admin already exists")
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        self.stdout.write(self.style.SUCCESS("Admin user created"))