from django.urls import path
from . import views

app_name = "organizations"

urlpatterns = [
    path("", views.organization_list, name="list"),
    path("create/", views.organization_create, name="create"),
    path("<int:pk>/", views.organization_detail, name="detail"),
    path("<int:pk>/edit/", views.organization_update, name="update"),
    path("<int:pk>/archive/", views.organization_archive, name="archive"),
    path("<int:pk>/restore/", views.organization_restore, name="restore"),
]