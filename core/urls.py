from django.urls import path
from .views import dashboard, AppLoginView, AppLogoutView

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("login/", AppLoginView.as_view(), name="login"),
    path("logout/", AppLogoutView.as_view(), name="logout"),
]