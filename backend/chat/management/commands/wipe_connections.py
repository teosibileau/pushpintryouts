from django.core.management.base import BaseCommand

from chat.models import Connection


class Command(BaseCommand):
    help = (
        "Delete all connection rows. Run after a cold start of the stack "
        "(Pushpin lost every socket, so the rows are stale); never while "
        "Pushpin is holding live connections."
    )

    def handle(self, *args, **options):
        deleted, _ = Connection.objects.all().delete()
        self.stdout.write(f"wiped {deleted} connection(s)")
