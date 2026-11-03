from urllib.parse import urlencode
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from accounts.decorators import role_required
from accounts.models import Preference
from matching.models import Notification, Review
from matching.utils import haversine_km
from .forms import RoomForm
from .models import Amenity, RentalRequest, Room, RoomImage


def _reference_point(request):
    """Point used for distance: ?lat&lng, else tenant preference, else profile location."""
    try:
        return float(request.GET["lat"]), float(request.GET["lng"])
    except (KeyError, ValueError):
        pass
    if request.user.is_authenticated:
        pref = Preference.get_preference(request.user)
        if pref and pref.latitude is not None:
            return pref.latitude, pref.longitude
        profile = getattr(request.user, "profile", None)
        if profile and profile.get_location():
            return profile.get_location()
    return None


# ---------- public / tenant ----------
def room_list(request):
    g = request.GET
    qs = Room.objects.prefetch_related("images", "amenities").select_related("owner__profile")
    if g.get("q"):
        qs = qs.filter(Q(title__icontains=g["q"]) | Q(location__icontains=g["q"]) | Q(description__icontains=g["q"]))
    if g.get("min_rent"):
        qs = qs.filter(rent__gte=g["min_rent"])
    if g.get("max_rent"):
        qs = qs.filter(rent__lte=g["max_rent"])
    if g.get("room_type"):
        qs = qs.filter(room_type=g["room_type"])
    for amenity_id in g.getlist("amenity"):
        qs = qs.filter(amenities__id=amenity_id)           # must have ALL selected
    if g.get("available", "1") == "1":
        qs = qs.filter(is_available=True)

    rooms = list(qs.distinct())
    ref = _reference_point(request)
    for r in rooms:
        r.distance = haversine_km(ref, r.get_location()) if ref else None
    sort = g.get("sort", "newest")
    if sort == "rent_low":
        rooms.sort(key=lambda r: r.rent)
    elif sort == "rent_high":
        rooms.sort(key=lambda r: -r.rent)
    elif sort == "distance" and ref:
        rooms.sort(key=lambda r: r.distance)

    params = g.copy()
    params.pop("page", None)
    page = Paginator(rooms, 9).get_page(g.get("page"))
    return render(request, "rooms/room_list.html", {
        "page": page, "amenities": Amenity.objects.all(), "types": Room._meta.get_field("room_type").choices,
        "selected_amenities": g.getlist("amenity"), "querystring": urlencode(params, doseq=True),
        "g": g, "has_ref": ref is not None, "total": len(rooms),
    })


def room_detail(request, pk):
    room = get_object_or_404(Room.objects.prefetch_related("images", "amenities"), pk=pk)
    rental, can_review = None, False
    if request.user.is_authenticated and getattr(request.user, "profile", None) and request.user.profile.role == "tenant":
        rental = RentalRequest.objects.filter(tenant=request.user, room=room).first()
        can_review = bool(rental and rental.status == "accepted")
    return render(request, "rooms/room_detail.html", {
        "room": room, "rental": rental, "can_review": can_review,
        "show_phone": bool(rental and rental.status == "accepted"),
        "reviews": room.reviews.select_related("from_user__profile"),
        "avg": Review.get_average_rating(room.owner),
    })


@role_required("tenant")
@require_POST
def send_rental_request(request, pk):
    room = get_object_or_404(Room, pk=pk, is_available=True)
    req, created = RentalRequest.objects.get_or_create(
        tenant=request.user, room=room, defaults={"message": request.POST.get("message", "")})
    if created:
        Notification.notify(room.owner, f"{request.user.profile.name} requested '{room.title}'", reverse("rooms:owner_requests"))
        messages.success(request, "Rental request sent to the owner.")
    else:
        messages.info(request, "You already requested this room.")
    return redirect("rooms:detail", pk=pk)


@role_required("tenant")
@require_POST
def add_review(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if RentalRequest.objects.filter(tenant=request.user, room=room, status="accepted").exists():
        rating = min(5, max(1, int(request.POST.get("rating", 5))))
        Review.objects.create(from_user=request.user, to_user=room.owner, room=room,
                              rating=rating, comment=request.POST.get("comment", ""))
        messages.success(request, "Thanks for your review!")
    return redirect("rooms:detail", pk=pk)


# ---------- owner ----------
@role_required("owner")
def owner_rooms(request):
    rooms = Room.objects.filter(owner=request.user).prefetch_related("images")
    return render(request, "rooms/owner_rooms.html", {"rooms": rooms})


@role_required("owner")
def room_form(request, pk=None):
    room = get_object_or_404(Room, pk=pk, owner=request.user) if pk else None
    form = RoomForm(request.POST or None, instance=room)
    if request.method == "POST" and form.is_valid():
        room = form.save(commit=False)
        room.owner = request.user
        room.save()
        form.save_m2m()
        has_primary = room.images.filter(is_primary=True).exists()
        for i, f in enumerate(request.FILES.getlist("images")):      # multiple upload
            RoomImage.objects.create(room=room, image=f, is_primary=(not has_primary and i == 0))
        messages.success(request, "Property saved.")
        return redirect("rooms:owner_rooms")
    return render(request, "rooms/room_form.html", {"form": form, "room": room})



def _own_room(request, pk):
    return get_object_or_404(Room, pk=pk, owner=request.user)


@role_required("owner")
@require_POST
def room_delete(request, pk):
    _own_room(request, pk).delete()
    messages.info(request, "Property deleted.")
    return redirect("rooms:owner_rooms")


@role_required("owner")
@require_POST
def room_toggle(request, pk):
    room = _own_room(request, pk)
    room.is_available = not room.is_available
    room.save(update_fields=["is_available"])
    return redirect("rooms:owner_rooms")


@role_required("owner")
@require_POST
def image_delete(request, pk):
    img = get_object_or_404(RoomImage, pk=pk, room__owner=request.user)
    room_id = img.room_id
    img.delete()
    return redirect("rooms:edit", pk=room_id)


@role_required("owner")
@require_POST
def image_primary(request, pk):
    img = get_object_or_404(RoomImage, pk=pk, room__owner=request.user)
    img.set_primary()
    return redirect("rooms:edit", pk=img.room_id)


@role_required("owner")
def owner_requests(request):
    reqs = RentalRequest.objects.filter(room__owner=request.user).select_related("tenant__profile", "room")
    return render(request, "rooms/owner_requests.html", {"reqs": reqs})


@role_required("owner")
@require_POST
def request_action(request, pk, action):
    req = get_object_or_404(RentalRequest, pk=pk, room__owner=request.user)
    if action in ("accepted", "rejected"):
        req.status = action
        req.save(update_fields=["status"])
        Notification.notify(req.tenant, f"Your request for '{req.room.title}' was {action}",
                            reverse("rooms:detail", args=[req.room_id]))
    return redirect("rooms:owner_requests")
