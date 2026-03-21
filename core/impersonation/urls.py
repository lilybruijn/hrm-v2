from django.urls import path
from .views import impersonate_start, impersonate_stop

app_name = "impersonation"

urlpatterns = [
    path("<int:user_id>/start/", impersonate_start, name="start"),
    path("stop/", impersonate_stop, name="stop"),
]