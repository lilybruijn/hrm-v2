from django.urls import path
from . import views

app_name = "wage_values"

urlpatterns = [
    path("", views.wage_value_list, name="list"),
    path("create/", views.wage_value_create, name="create"),
    path("<int:pk>/", views.wage_value_detail, name="detail"),
    path("<int:pk>/edit/", views.wage_value_update, name="update"),
    path("<int:pk>/archive/", views.wage_value_archive, name="archive"),
    path("<int:pk>/restore/", views.wage_value_restore, name="restore"),
]