from django.urls import path
from . import views

app_name = "matching"

urlpatterns = [
    path("matches/", views.matches, name="matches"),
    path("matches/<int:pk>/<str:action>/", views.match_action, name="match_action"),
    path("roommates/", views.roommate_requests, name="roommate_requests"),
    path("roommates/send/<int:user_id>/", views.send_roommate_request, name="send_request"),
    path("roommates/<int:pk>/<str:action>/", views.roommate_respond, name="roommate_respond"),
    path("notifications/", views.notifications, name="notifications"),
]
