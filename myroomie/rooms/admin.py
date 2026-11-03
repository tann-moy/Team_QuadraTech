from django.contrib import admin
from .models import Amenity, RentalRequest, Room, RoomImage


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "location", "rent", "room_type", "is_available")
    list_filter = ("room_type", "is_available", "amenities")
    search_fields = ("title", "location")
    inlines = [RoomImageInline]


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "icon")


@admin.register(RentalRequest)
class RentalRequestAdmin(admin.ModelAdmin):
    list_display = ("tenant", "room", "status", "created_at")
    list_filter = ("status",)
