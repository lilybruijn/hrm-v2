from django.core.management.base import BaseCommand
from django.db import transaction

# from core.models import Person  # pas aan op jouw models
# class Command(BaseCommand):
    #help = "Seed minimal test data"

   # @transaction.atomic
    #def handle(self, *args, **options):
     #   if Person.objects.exists():
        #    self.stdout.write("Seed skipped (already has data).")
         #   return

       # self.stdout.write(self.style.SUCCESS("Seed completed."))