from django.urls import path, include
from .views import dashboard, AppLoginView, AppLogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("login/", AppLoginView.as_view(), name="login"),
    path("logout/", AppLogoutView.as_view(), name="logout"),

    ## SIGNALS
    path("signals/", include("core.signals.urls", namespace="signals")),

    ## ACTIVITIES
    path("activities/", include("core.activities.urls", namespace="activities")),

    ## PEOPLE
    path("people/", include("core.people.urls", namespace="people")),

    ## TASKS
    path("tasks/", include("core.tasks.urls")),

    ## SETTINGS
    path("settings/", include("core.settings.urls")),

    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)