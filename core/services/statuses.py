from core.models.status import StatusUsage, Status

def get_default_status_for(module_key: str) -> Status | None:
    usage = StatusUsage.objects.select_related("status_set").filter(module_key=module_key, enabled=True).first()
    if not usage or not usage.status_set:
        return None
    return Status.objects.filter(status_set=usage.status_set, is_default=True).first()