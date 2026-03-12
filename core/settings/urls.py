from django.urls import path, include
from . import views

app_name = "settings"

urlpatterns = [
    path("", views.settings_index, name="index"),

    path("signal-types/", views.signal_status_list, name="signal_type_list"),
    path("signal-types/new/", views.signal_status_create, name="signal_type_create"),
    path("signal-types/<int:pk>/edit/", views.signal_status_update, name="signal_type_update"),
    path("signal-types/<int:pk>/archive/", views.signal_status_archive, name="signal_type_archive"),
    path("signal-types/<int:pk>/restore/", views.signal_status_restore, name="signal_type_restore"),
    path("signal-types/<int:pk>/delete/", views.signal_status_delete, name="signal_type_delete"),

    path("signal-statuses/", views.signal_status_list, name="signal_status_list"),
    path("signal-statuses/new/", views.signal_status_create, name="signal_status_create"),
    path("signal-statuses/<int:pk>/edit/", views.signal_status_update, name="signal_status_update"),
    path("signal-statuses/<int:pk>/archive/", views.signal_status_archive, name="signal_status_archive"),
    path("signal-statuses/<int:pk>/restore/", views.signal_status_restore, name="signal_status_restore"),
    path("signal-statuses/<int:pk>/delete/", views.signal_status_delete, name="signal_status_delete"),

    path("task-types/", views.task_type_list, name="task_type_list"),
    path("task-types/new/", views.task_type_create, name="task_type_create"),
    path("task-types/<int:pk>/edit/", views.task_type_update, name="task_type_update"),
    path("task-types/<int:pk>/archive/", views.task_type_archive, name="task_type_archive"),
    path("task-types/<int:pk>/restore/", views.task_type_restore, name="task_type_restore"),
    path("task-types/<int:pk>/delete/", views.task_type_delete, name="task_type_delete"),

    path("task-statuses/", views.task_status_list, name="task_status_list"),
    path("task-statuses/new/", views.task_status_create, name="task_status_create"),
    path("task-statuses/<int:pk>/edit/", views.task_status_update, name="task_status_update"),
    path("task-statuses/<int:pk>/archive/", views.task_status_archive, name="task_status_archive"),
    path("task-statuses/<int:pk>/restore/", views.task_status_restore, name="task_status_restore"),
    path("task-statuses/<int:pk>/delete/", views.task_status_delete, name="task_status_delete"),

    
]