from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

User = get_user_model()


class ImpersonateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.real_user = request.user
        request.is_impersonating = False

        impersonate_user_id = request.session.get("impersonate_user_id")
        impersonator_id = request.session.get("impersonator_id")

        if (
            impersonate_user_id
            and impersonator_id
            and request.user.is_authenticated
            and request.user.id == impersonator_id
        ):
            try:
                impersonated_user = User.objects.get(pk=impersonate_user_id, is_active=True)
                request.real_user = request.user
                request.user = impersonated_user
                request.is_impersonating = True
            except User.DoesNotExist:
                request.session.pop("impersonate_user_id", None)
                request.session.pop("impersonator_id", None)

        return self.get_response(request)