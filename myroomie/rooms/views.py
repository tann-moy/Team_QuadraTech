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
