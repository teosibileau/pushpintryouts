from __future__ import annotations

from chat.models import Connection, Message


def message_list_recent(*, limit: int = 50) -> list[Message]:
    return list(
        reversed(Message.objects.select_related("user").order_by("-created_at")[:limit])
    )


def online_usernames() -> list[str]:
    return list(
        Connection.objects.select_related("user")
        .values_list("user__username", flat=True)
        .distinct()
        .order_by("user__username")
    )
