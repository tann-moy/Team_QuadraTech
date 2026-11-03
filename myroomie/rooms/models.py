from django.contrib.auth.models import User
from django.db import models
from accounts.models import Preference


class Amenity(models.Model):
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=40, default="bi-check-circle", help_text="Bootstrap icon class")

    class Meta:
        verbose_name_plural = "amenities"

    def __str__(self):
        return self.name


class Room(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rooms")
    title = models.CharField(max_length=150)
    description = models.TextField()
    location = models.CharField("Address / area", max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    rent = models.PositiveIntegerField("Monthly rent (৳)")
    room_type = models.CharField(max_length=10, choices=Preference.ROOM_TYPES, default="single")
    available_from = models.DateField()
    is_available = models.BooleanField(default=True)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="rooms")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_room_details(self):
        return {"title": self.title, "rent": self.rent, "type": self.get_room_type_display(),
                "location": self.location, "available_from": self.available_from}

    def get_images(self):
        return self.images.all()

    def get_primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    def get_amenities(self):
        return self.amenities.all()

    def get_location(self):
        return (self.latitude, self.longitude)


