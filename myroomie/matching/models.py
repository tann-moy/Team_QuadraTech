from django.contrib.auth.models import User
from django.db import models
from accounts.models import Preference
from rooms.models import Room
from .utils import calculate_compatibility, compatibility_breakdown, haversine_km


class Match(models.Model):
    STATUS = [("suggested", "Suggested"), ("accepted", "Accepted"), ("rejected", "Rejected")]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="matches")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    matched_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="matched_with")
    compatibility_score = models.FloatField(default=0)
    status = models.CharField(max_length=10, choices=STATUS, default="suggested")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "matched_user")
        ordering = ["-compatibility_score"]

    def __str__(self):
        return f"{self.user} ~ {self.matched_user} ({self.compatibility_score}%)"

    def _prefs(self):
        return Preference.get_preference(self.user), Preference.get_preference(self.matched_user)

    def calculate_match(self):
        a, b = self._prefs()
        self.compatibility_score = calculate_compatibility(a, b)
        self.save(update_fields=["compatibility_score"])
        return self.compatibility_score

    def get_match_details(self):
        a, b = self._prefs()
        return compatibility_breakdown(a, b)

    def update_status(self, status):
        self.status = status
        self.save(update_fields=["status"])

    def calculate_distance(self):
        a, b = self._prefs()
        return haversine_km((a.latitude, a.longitude), (b.latitude, b.longitude))

    def find_nearby_rooms(self, radius_km=5):
        a, b = self._prefs()
        mid = ((a.latitude + b.latitude) / 2, (a.longitude + b.longitude) / 2)
        rooms = []
        for room in Room.objects.filter(is_available=True).select_related("owner__profile"):
            room.distance = haversine_km(mid, (room.latitude, room.longitude))
            if room.distance <= radius_km:
                rooms.append(room)
        return self.sort_by_distance(rooms)

    @staticmethod
    def sort_by_distance(rooms):
        return sorted(rooms, key=lambda r: r.distance)


class Review(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews_given")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews_received")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(default=5)   # 1-5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.from_user} -> {self.to_user}: {self.rating}/5"

    @staticmethod
    def get_average_rating(user):
        return Review.objects.filter(to_user=user).aggregate(a=models.Avg("rating"))["a"]


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def notify(cls, user, message, link=""):
        return cls.objects.create(user=user, message=message, link=link)
