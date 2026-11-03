from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.RoleLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("tenant/", views.tenant_dashboard, name="tenant_dashboard"),
    path("owner/", views.owner_dashboard, name="owner_dashboard"),
    path("profile/", views.profile_edit, name="profile"),
    path("preference/", views.preference_edit, name="preference"),
    path("preference/delete/", views.preference_delete, name="preference_delete"),
]
