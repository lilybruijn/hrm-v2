from django.urls import path
from . import views

app_name = "documents"

urlpatterns = [
    path("templates/", views.template_list, name="template_list"),
    path("templates/create/", views.template_create, name="template_create"),
    path("templates/<int:pk>/", views.template_detail, name="template_detail"),
    path("templates/<int:pk>/edit/", views.template_update, name="template_update"),
    path("templates/<int:pk>/archive/", views.template_archive, name="template_archive"),
    path("templates/<int:pk>/restore/", views.template_restore, name="template_restore"),
    path("templates/<int:pk>/delete/", views.template_delete, name="template_delete"),
    path("templates/<int:template_pk>/variables/create/", views.template_variable_create, name="template_variable_create"),
    path("templates/<int:pk>/scan-placeholders/", views.template_scan_placeholders, name="template_scan_placeholders"),

    path("variables/<int:pk>/edit/", views.template_variable_update, name="template_variable_update"),
    path("variables/<int:pk>/archive/", views.template_variable_archive, name="template_variable_archive"),
    path("variables/<int:pk>/restore/", views.template_variable_restore, name="template_variable_restore"),
    path("variables/<int:pk>/delete/", views.template_variable_delete, name="template_variable_delete"),

    path("people/<int:person_pk>/create/", views.person_document_create, name="person_document_create"),
    path("document/<int:document_pk>/variables/", views.person_document_variables, name="document_variables"),
    path("document/<int:pk>/", views.document_detail, name="document_detail"),
    path("document/<int:pk>/regenerate/", views.document_regenerate, name="document_regenerate"),

    
]