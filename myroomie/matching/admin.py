from django.contrib import admin
from .models import Match, Notification, Review


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("user", "matched_user", "compatibility_score", "status", "created_at")
    list_filter = ("status",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "room", "rating", "created_at")
    list_filter = ("rating",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "is_read", "created_at")
    list_filter = ("is_read",)
