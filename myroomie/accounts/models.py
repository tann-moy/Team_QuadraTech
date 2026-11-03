from datetime import time
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = [("tenant", "Tenant"), ("owner", "Owner")]
    ID_TYPES = [("nid", "National ID card"), ("birth_certificate", "Birth certificate")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    name = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    organization = models.CharField("University / College / Company", max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    # Admin must tick is_verified before this user can log in
    is_verified = models.BooleanField(default=False, help_text="Tick after checking the ID document. Unverified users cannot log in.")
    id_type = models.CharField("ID type", max_length=20, choices=ID_TYPES, blank=True)
    id_document = models.ImageField("NID / birth certificate photo", upload_to="id_documents/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ref_loc = models.CharField("Reference location", max_length=200, blank=True)
    ref_latitude = models.FloatField(null=True, blank=True)
    ref_longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.role})"

    def get_location(self):
        if self.ref_latitude is None or self.ref_longitude is None:
            return None
        return (self.ref_latitude, self.ref_longitude)

    def get_room(self):
        return self.user.rooms.all() if hasattr(self.user, "rooms") else []

    def get_sent_requests(self):
        return self.user.sent_roommate_requests.all()

    def get_received_requests(self):
        return self.user.received_roommate_requests.all()


class Preference(models.Model):
    GENDER = [("male", "Male"), ("female", "Female"), ("other", "Other")]
    FOOD = [("veg", "Vegetarian"), ("non_veg", "Non-vegetarian")]
    SMOKING = [("smoker", "Smoker"), ("non_smoker", "Non-smoker")]
    CLEANLINESS = [("not_clean", "Not clean"), ("clean", "Clean"), ("very_clean", "Very clean")]
    ROOM_TYPES = [("single", "Single room"), ("shared", "Shared room"), ("flat", "Full flat")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preference")
    location_name = models.CharField("Preferred area", max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    budget_min = models.PositiveIntegerField(default=0)
    budget_max = models.PositiveIntegerField(default=0)
    gender = models.CharField(max_length=10, choices=GENDER)   # matching: same gender only
    food_type = models.CharField(max_length=10, choices=FOOD)
    smoking = models.CharField(max_length=12, choices=SMOKING)
    cleanliness = models.CharField(max_length=12, choices=CLEANLINESS, default="clean")
    sleep_time = models.TimeField(default=time(23, 0))          # usual bed time
    preferred_room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default="single")
    additional_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Preference of {self.user.username}"

    @classmethod
    def get_preference(cls, user):
        return cls.objects.filter(user=user).first()


class RoommateRequest(models.Model):
    STATUS = [("pending", "Pending"), ("accepted", "Accepted"), ("rejected", "Rejected")]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_roommate_requests")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_roommate_requests")
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("sender", "receiver")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender} -> {self.receiver} [{self.status}]"

    @classmethod
    def send_request(cls, sender, receiver, message=""):
        return cls.objects.get_or_create(sender=sender, receiver=receiver, defaults={"message": message})

    def accept_request(self):
        self.status = "accepted"
        self.save(update_fields=["status"])

    def reject_request(self):
        self.status = "rejected"
        self.save(update_fields=["status"])

    def get_status(self):
        return self.get_status_display()
