from django.contrib import admin
from django.utils.html import format_html

from .models import Preference, RoommateRequest, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "role", "phone", "id_type", "is_verified", "created_at")
    list_editable = ("is_verified",)                     # tick the box right in the list
    list_filter = ("is_verified", "role", "id_type")
    search_fields = ("name", "user__username", "phone")
    ordering = ("is_verified", "-created_at")            # unverified users first
    readonly_fields = ("id_preview",)
    actions = ["verify_selected", "unverify_selected"]

    @admin.display(description="ID document")
    def id_preview(self, obj):
        if not obj.id_document:
            return "No document uploaded"
        return format_html('<a href="{0}" target="_blank"><img src="{0}" style="max-height:320px;border-radius:8px"></a>',
                           obj.id_document.url)

    @admin.action(description="Verify selected users")
    def verify_selected(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_verified=True)} user(s) verified.")

    @admin.action(description="Remove verification")
    def unverify_selected(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_verified=False)} user(s) un-verified.")


@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "location_name", "budget_min", "budget_max", "gender", "food_type", "smoking")
    list_filter = ("gender", "food_type", "smoking", "cleanliness")


@admin.register(RoommateRequest)
class RoommateRequestAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "status", "created_at")
    list_filter = ("status",)
