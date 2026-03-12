from django.urls import path
from . import views

app_name = "jobcoaching"

urlpatterns = [
    path("", views.jobcoaching_list, name="list"),
    path("create/", views.jobcoaching_create, name="create"),
    path("<int:pk>/", views.jobcoaching_detail, name="detail"),
    path("<int:pk>/edit/", views.jobcoaching_update, name="update"),
    path("<int:pk>/archive/", views.jobcoaching_archive, name="archive"),
    path("<int:pk>/restore/", views.jobcoaching_restore, name="restore"),
]