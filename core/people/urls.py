from django.urls import path
from . import views

app_name = "people"

urlpatterns = [
    path("", views.person_list, name="list"),
    path("new/", views.person_create, name="create"),
    path("<int:pk>/", views.person_detail, name="detail"),
    path("<int:pk>/update/", views.person_update, name="update"),
    path("<int:pk>/note/", views.person_add_note, name="add_note"),
]