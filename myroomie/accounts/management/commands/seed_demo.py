"""python manage.py seed_demo  ->  sample owners, tenants, rooms (password for all: 1234)."""
from datetime import date, time

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Preference, UserProfile
from rooms.models import Amenity, Room

AMENITIES = [("WiFi", "bi-wifi"), ("Attached bath", "bi-droplet"), ("Gas", "bi-fire"),
             ("Lift", "bi-arrow-up-square"), ("Generator", "bi-lightning-charge"),
             ("Furnished", "bi-lamp"), ("Security", "bi-shield-check")]
OWNERS = [("owner_rahim", "Rahim Uddin"), ("owner_karim", "Karim Hossain"), ("owner_salma", "Salma Begum")]
ROOMS = [  # title, area, lat, lng, rent, type, owner index
    ("Sunny single room", "Dhanmondi 27", 23.7461, 90.3742, 7000, "single", 0),
    ("Shared room near campus", "Mohammadpur", 23.7662, 90.3589, 4500, "shared", 1),
    ("Modern flat with balcony", "Uttara Sector 7", 23.8759, 90.3795, 16000, "flat", 2),
    ("Cozy room, quiet street", "Mirpur 10", 23.8069, 90.3687, 5500, "single", 0),
    ("Budget shared room", "Farmgate", 23.7561, 90.3872, 3500, "shared", 1),
    ("Furnished room, lift", "Banani", 23.7937, 90.4066, 12000, "single", 2),
]
# username, name, gender, food, smoking, cleanliness, sleep, budget, (lat,lng), area
TENANTS = [
    ("rafi", "Rafi Ahmed", "male", "non_veg", "non_smoker", "clean", time(23, 0), (5000, 8000), (23.7500, 90.3750), "Dhanmondi"),
    ("tanvir", "Tanvir Islam", "male", "non_veg", "non_smoker", "clean", time(23, 30), (5000, 8500), (23.7650, 90.3600), "Mohammadpur"),
    ("sakib", "Sakib Khan", "male", "veg", "smoker", "not_clean", time(2, 0), (3000, 5000), (23.8100, 90.3700), "Mirpur"),
    ("nabila", "Nabila Rahman", "female", "veg", "non_smoker", "very_clean", time(22, 0), (6000, 10000), (23.7930, 90.4060), "Banani"),
    ("mim", "Mim Akter", "female", "veg", "non_smoker", "very_clean", time(22, 30), (6000, 9000), (23.7900, 90.4000), "Gulshan"),
    ("arif", "Arif Hasan", "male", "non_veg", "non_smoker", "very_clean", time(0, 0), (4500, 7500), (23.7560, 90.3860), "Farmgate"),
]


class Command(BaseCommand):
    help = "Create demo data"

    def handle(self, *args, **opts):
        amen = [Amenity.objects.get_or_create(name=n, defaults={"icon": i})[0] for n, i in AMENITIES]
        owners = []
        for uname, name in OWNERS:
            u, new = User.objects.get_or_create(username=uname)
            if new:
                u.set_password("1234"); u.save()
                UserProfile.objects.create(user=u, name=name, role="owner", phone="01700000000", is_verified=True)
            owners.append(u)
        if not Room.objects.exists():
            for i, (title, area, lat, lng, rent, rtype, o) in enumerate(ROOMS):
                r = Room.objects.create(owner=owners[o], title=title, description="Clean, airy and close to transport, shops and eateries.",
                                        location=area, latitude=lat, longitude=lng, rent=rent, room_type=rtype,
                                        available_from=date.today())
                r.amenities.set(amen[: 3 + i % 4])
        for uname, name, g, food, smoke, clean, sleep, (bmin, bmax), (lat, lng), area in TENANTS:
            u, new = User.objects.get_or_create(username=uname)
            if new:
                u.set_password("1234"); u.save()
                UserProfile.objects.create(user=u, name=name, role="tenant", phone="01800000000", organization="Dhaka University", is_verified=True)
                Preference.objects.create(user=u, gender=g, food_type=food, smoking=smoke, cleanliness=clean,
                                          sleep_time=sleep, budget_min=bmin, budget_max=bmax, latitude=lat,
                                          longitude=lng, location_name=area)
        demo_names = [u for u, _ in OWNERS] + [t[0] for t in TENANTS]
        UserProfile.objects.filter(user__username__in=demo_names).update(is_verified=True)
        self.stdout.write(self.style.SUCCESS("Demo data ready. Logins: rafi / owner_rahim ... password 1234"))
