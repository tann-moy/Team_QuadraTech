from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from .decorators import role_required
from .forms import PreferenceForm, RegisterForm, UserProfileForm, VerifiedAuthenticationForm
from .models import Preference
from matching.models import Match
from matching.services import generate_matches
from rooms.models import RentalRequest, Room


def home(request):
    return render(request, "home.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = RegisterForm(request.POST or None, request.FILES or None)   # FILES = uploaded ID image
    if request.method == "POST" and form.is_valid():
        form.save()                                                   # no auto-login
        messages.success(request, "Account created! You can log in after the admin verifies your ID.")
        return redirect("accounts:login")
    return render(request, "accounts/register.html", {"form": form})


class RoleLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = VerifiedAuthenticationForm
    redirect_authenticated_user = True


@login_required
def dashboard(request):
    """Send each user to their own dashboard."""
    profile = getattr(request.user, "profile", None)
    if profile is None:                      # e.g. a superuser without profile
        return redirect("admin:index")
    return redirect("accounts:owner_dashboard" if profile.role == "owner" else "accounts:tenant_dashboard")


@role_required("tenant")
def tenant_dashboard(request):
    pref = Preference.get_preference(request.user)
    generate_matches(request.user)
    return render(request, "accounts/tenant_dashboard.html", {
        "preference": pref,
        "match_count": Match.objects.filter(user=request.user, status="suggested").count(),
        "top_matches": Match.objects.filter(user=request.user).exclude(status="rejected").select_related("matched_user__profile")[:3],
        "rental_requests": RentalRequest.objects.filter(tenant=request.user).select_related("room")[:5],
        "requests_sent": request.user.profile.get_sent_requests().count(),
        "requests_received": request.user.profile.get_received_requests().count(),
    })


@role_required("owner")
def owner_dashboard(request):
    rooms = Room.objects.filter(owner=request.user)
    pending = RentalRequest.objects.filter(room__owner=request.user, status="pending").select_related("tenant__profile", "room")
    return render(request, "accounts/owner_dashboard.html", {
        "room_count": rooms.count(), "vacant_count": rooms.filter(is_available=True).count(),
        "pending_count": pending.count(), "pending": pending[:5],
    })


@login_required
def profile_edit(request):
    form = UserProfileForm(request.POST or None, request.FILES or None, instance=request.user.profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})


@role_required("tenant")
def preference_edit(request):
    form = PreferenceForm(request.POST or None, instance=Preference.get_preference(request.user))
    if request.method == "POST" and form.is_valid():
        pref = form.save(commit=False)
        pref.user = request.user
        pref.save()
        messages.success(request, "Preferences saved.")
        return redirect("accounts:tenant_dashboard")
    return render(request, "accounts/preference.html", {"form": form})


@role_required("tenant")
@require_POST
def preference_delete(request):
    Preference.objects.filter(user=request.user).delete()
    messages.info(request, "Preferences deleted.")
    return redirect("accounts:tenant_dashboard")
