"""Notifications module."""
from notifications.service import notification_service, NotificationService
from notifications.templates import notification_templates

__all__ = [
    "notification_service",
    "NotificationService",
    "notification_templates",
]
