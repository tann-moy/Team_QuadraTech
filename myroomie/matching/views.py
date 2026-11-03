from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from accounts.decorators import role_required
from accounts.models import Preference, RoommateRequest
from .models import Match, Notification
from .services import generate_matches


@role_required("tenant")
def matches(request):
    if not Preference.get_preference(request.user):
        messages.warning(request, "Set your preferences first to get roommate matches.")
        return redirect("accounts:preference")
    generate_matches(request.user)
    items = Match.objects.filter(user=request.user).exclude(status="rejected").filter(matched_user__preference__isnull=False).select_related("matched_user__profile")
    for m in items:
        m.nearby = m.find_nearby_rooms()[:3]
        m.distance_km = m.calculate_distance()
        m.pref = Preference.get_preference(m.matched_user)
        m.req = RoommateRequest.objects.filter(
            Q(sender=request.user, receiver=m.matched_user) | Q(sender=m.matched_user, receiver=request.user)).first()
    return render(request, "matching/matches.html", {"items": items})


@role_required("tenant")
@require_POST
def match_action(request, pk, action):
    match = get_object_or_404(Match, pk=pk, user=request.user)
    if action in ("accepted", "rejected"):
        match.update_status(action)
    return redirect("matching:matches")


@role_required("tenant")
@require_POST
def send_roommate_request(request, user_id):
    receiver = get_object_or_404(User, pk=user_id, profile__role="tenant")
    req, created = RoommateRequest.send_request(request.user, receiver, request.POST.get("message", ""))
    if created:
        Notification.notify(receiver, f"{request.user.profile.name} sent you a roommate request",
                            reverse("matching:roommate_requests"))
        messages.success(request, "Roommate request sent.")
    else:
        messages.info(request, "You already sent a request to this person.")
    return redirect("matching:matches")


@role_required("tenant")
def roommate_requests(request):
    return render(request, "matching/requests.html", {
        "received": RoommateRequest.objects.filter(receiver=request.user).select_related("sender__profile"),
        "sent": RoommateRequest.objects.filter(sender=request.user).select_related("receiver__profile"),
    })


@role_required("tenant")
@require_POST
def roommate_respond(request, pk, action):
    req = get_object_or_404(RoommateRequest, pk=pk, receiver=request.user)
    if action == "accept":
        req.accept_request()
    elif action == "reject":
        req.reject_request()
    Notification.notify(req.sender, f"{request.user.profile.name} {req.status} your roommate request",
                        reverse("matching:roommate_requests"))
    return redirect("matching:roommate_requests")


@role_required("tenant")
def notifications(request):
    items = list(request.user.notifications.all()[:50])
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, "matching/notifications.html", {"items": items})
