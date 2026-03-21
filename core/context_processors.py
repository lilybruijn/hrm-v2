def impersonation_context(request):
    return {
        "is_impersonating": getattr(request, "is_impersonating", False),
        "real_user": getattr(request, "real_user", None),
    }