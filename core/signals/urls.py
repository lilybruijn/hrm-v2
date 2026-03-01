from django.urls import path
from . import views

app_name = "signals"

urlpatterns = [
    path("", views.signal_list, name="list"),
    path("new/", views.signal_create, name="create"),
    path("<int:pk>/", views.signal_detail, name="detail"),
    path("<int:pk>/update/", views.signal_update, name="signal_update"),
    path("<int:pk>/status/", views.signal_set_status, name="set_status"),
    path("<int:pk>/type/", views.signal_set_type, name="set_type"),
    path("<int:pk>/active-from/", views.signal_set_active_from, name="set_active_from"),
    path("<int:pk>/assign/", views.signal_set_assignee, name="set_assignee"),
    path("<int:pk>/note/", views.signal_add_note, name="add_note"),
    path("<int:pk>/archive/", views.signal_toggle_archive, name="toggle_archive"),
]