from django.apps import AppConfig
from django.db.utils import Error as DBError


class ChatConfig(AppConfig):
    name = "chat"

    def ready(self):
        # A fresh boot means no sockets can be alive (Pushpin's connections
        # die with the stack), so stale rows are safe to clear. Gunicorn runs
        # ready() per worker; the delete is idempotent.
        import sys

        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            return
        try:
            from chat.models import Connection

            Connection.objects.all().delete()
        except DBError:
            pass
