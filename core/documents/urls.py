from django.urls import path
from . import views

app_name = "documents"

urlpatterns = [
    path("templates/", views.template_list, name="template_list"),
    path("templates/create/", views.template_create, name="template_create"),
    path("templates/<int:pk>/", views.template_detail, name="template_detail"),
    path("templates/<int:template_pk>/variables/create/", views.template_variable_create, name="template_variable_create"),
    path("templates/<int:pk>/archive/", views.template_archive, name="template_archive"),
    path("templates/<int:pk>/restore/", views.template_restore, name="template_restore"),
    path("templates/<int:pk>/delete/", views.template_delete, name="template_delete"),
    path("people/<int:person_pk>/create/", views.person_document_create, name="person_document_create"),
    path("document/<int:document_pk>/variables/", views.person_document_variables, name="document_variables"),
    
]