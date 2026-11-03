from django.urls import path
from . import views

app_name = "rooms"

urlpatterns = [
    path("", views.room_list, name="list"),
    path("<int:pk>/", views.room_detail, name="detail"),
    path("<int:pk>/request/", views.send_rental_request, name="send_request"),
    path("<int:pk>/review/", views.add_review, name="review"),
    path("manage/", views.owner_rooms, name="owner_rooms"),
    path("manage/new/", views.room_form, name="create"),
    path("manage/<int:pk>/edit/", views.room_form, name="edit"),
    path("manage/<int:pk>/delete/", views.room_delete, name="delete"),
    path("manage/<int:pk>/toggle/", views.room_toggle, name="toggle"),
    path("image/<int:pk>/delete/", views.image_delete, name="image_delete"),
    path("image/<int:pk>/primary/", views.image_primary, name="image_primary"),
    path("requests/", views.owner_requests, name="owner_requests"),
    path("requests/<int:pk>/<str:action>/", views.request_action, name="request_action"),
]
