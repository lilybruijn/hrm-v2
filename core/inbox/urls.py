from django.urls import path

from . import views

app_name = "inbox"

urlpatterns = [
    path("", views.thread_list, name="list"),
    path("new/", views.thread_create, name="create"),
    path("<int:pk>/", views.thread_detail, name="detail"),
    path("<int:pk>/reply/", views.thread_reply, name="reply"),
    path("<int:pk>/toggle-archive/", views.thread_toggle_archive, name="toggle_archive"),
    path("<int:pk>/mark-read/", views.thread_mark_read, name="mark_read"),
    path("<int:pk>/mark-unread/", views.thread_mark_unread, name="mark_unread"),
]