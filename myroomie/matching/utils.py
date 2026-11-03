from math import asin, cos, radians, sin, sqrt

WEIGHTS = {"budget": 35, "location": 25, "food": 10, "smoking": 10,
           "sleep": 10, "cleanliness": 5, "gender": 5}
MAX_KM = 10
MAX_SLEEP_GAP = 360
CLEAN_LEVELS = ["not_clean", "clean", "very_clean"]
THRESHOLD = 60


def haversine_km(a, b):
    lat1, lng1, lat2, lng2 = map(radians, [a[0], a[1], b[0], b[1]])
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def _budget(a, b):
    overlap = min(a.budget_max, b.budget_max) - max(a.budget_min, b.budget_min)
    union = max(a.budget_max, b.budget_max) - min(a.budget_min, b.budget_min)
    if union <= 0:
        return 100 if a.budget_min == b.budget_min else 0
    return max(0, overlap) / union * 100


def _location(a, b):
    if None in (a.latitude, a.longitude, b.latitude, b.longitude):
        return 0
    km = haversine_km((a.latitude, a.longitude), (b.latitude, b.longitude))
    return max(0, 100 - km / MAX_KM * 100)


def _sleep(a, b):
    def mins(t):
        return t.hour * 60 + t.minute
    gap = abs(mins(a.sleep_time) - mins(b.sleep_time))
    gap = min(gap, 1440 - gap)          # 23:00 and 01:00 are 2 hours apart
    return max(0, 100 - gap / MAX_SLEEP_GAP * 100)


def _clean(a, b):
    gap = abs(CLEAN_LEVELS.index(a.cleanliness) - CLEAN_LEVELS.index(b.cleanliness))
    return max(0, 100 - gap * 50)       # same=100, one step=50, two steps=0


def compatibility_breakdown(a, b):
    return {
        "budget": _budget(a, b),
        "location": _location(a, b),
        "food": 100 if a.food_type == b.food_type else 0,
        "smoking": 100 if a.smoking == b.smoking else 0,
        "sleep": _sleep(a, b),
        "cleanliness": _clean(a, b),
        "gender": 100 if a.gender == b.gender else 0,
    }


def calculate_compatibility(a, b):
    if a.gender != b.gender:
        return 0.0
    parts = compatibility_breakdown(a, b)
    return round(sum(parts[k] * w for k, w in WEIGHTS.items()) / 100, 1)
