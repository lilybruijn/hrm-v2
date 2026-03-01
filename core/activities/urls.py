from django.urls import path
from .views import activities_list

app_name = "activities"

urlpatterns = [
    path("", activities_list, name="list"),
]