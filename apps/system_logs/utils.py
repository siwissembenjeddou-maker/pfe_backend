from .models import SystemLog


def log_event(event: str, user=None, metadata=None):
    return SystemLog.objects.create(
        event=event,
        user=user,
        metadata=metadata or {},
    )
