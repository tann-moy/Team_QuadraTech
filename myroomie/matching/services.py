from django.urls import reverse
from accounts.models import Preference
from .models import Match, Notification
from .utils import THRESHOLD, calculate_compatibility


def generate_matches(user):
    mine = Preference.get_preference(user)
    if not mine:
        return
    for other in Preference.objects.exclude(user=user).select_related("user"):
        score = calculate_compatibility(mine, other)
        if score >= THRESHOLD:
            match, created = Match.objects.update_or_create(
                user=user, matched_user=other.user, defaults={"compatibility_score": score})
            if created:
                Notification.notify(user, f"New {score:.0f}% roommate match: {other.user.profile.name}",
                                    reverse("matching:matches"))
        else:
            Match.objects.filter(user=user, matched_user=other.user, status="suggested").delete()
