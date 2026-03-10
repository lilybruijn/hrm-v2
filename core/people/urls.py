from django.urls import path
from . import views

app_name = "people"

urlpatterns = [
    path("", views.person_list, name="list"),
    path("new/", views.person_create, name="create"),
    path("<int:pk>/", views.person_detail, name="detail"),
    path("<int:pk>/update/", views.person_update, name="update"),
    path("<int:pk>/note/", views.person_add_note, name="add_note"),
    path("<int:pk>/description/", views.person_update_description, name="person_update_description"),
    path("<int:pk>/toggle-archive/", views.person_toggle_archive, name="toggle_archive"),
    path("<int:pk>/archive_detail/", views.person_toggle_archive_detail, name="toggle_archive_detail"),
    path("<int:pk>/restore/", views.person_restore, name="restore"),
    path("<int:pk>/delete/", views.person_delete, name="delete"),
]