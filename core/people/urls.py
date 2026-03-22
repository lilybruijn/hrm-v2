from django.urls import path
from . import views

app_name = "people"

urlpatterns = [
    path("", views.person_list, name="list"),
    path("students/", views.student_list, name="students"),
    path("employees/", views.employee_list, name="employees"),
    path("archived/", views.archived_list, name="archived"),
    path("new/", views.person_create, name="create"),
    path("<int:pk>/", views.person_detail, name="detail"),
    path("<int:pk>/update/", views.person_update, name="update"),
    path("<int:pk>/note/", views.person_add_note, name="add_note"),
    path("<int:pk>/toggle-archive/", views.person_toggle_archive, name="toggle_archive"),
    path("<int:pk>/archive_detail/", views.person_toggle_archive_detail, name="toggle_archive_detail"),
    path("<int:pk>/restore/", views.person_restore, name="restore"),
    path("<int:pk>/delete/", views.person_delete, name="delete"),

    # HTMX partials
    path("<int:pk>/partials/description/", views.person_description_view_partial, name="description_view_partial"),
    path("<int:pk>/partials/description/edit/", views.person_description_edit_partial, name="description_edit_partial"),
    path("<int:pk>/partials/data/", views.person_data_view_partial, name="data_view_partial"),
    path("<int:pk>/partials/data/edit/", views.person_data_edit_partial, name="data_edit_partial"),

    path("<int:pk>/partials/student-profile/", views.person_student_profile_view_partial, name="student_profile_view_partial"),
    path("<int:pk>/partials/student-profile/edit/", views.person_student_profile_edit_partial, name="student_profile_edit_partial"),
]
