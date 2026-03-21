from core.models import Notification


from core.models import Task, Status, TaskType

from django.contrib.auth import get_user_model

User = get_user_model()


def create_task_notifications(task, actor, reassigned=False):
    if not task.assigned_to:
        return None

    if reassigned:
        title = "Taak aan jou toegewezen"
        message = f"{actor.username} heeft de taak aan je toegewezen."
    else:
        title = "Nieuwe taak toegewezen"
        message = f"{actor.username} heeft een taak aan je toegewezen."

    return Notification.objects.create(
        user=task.assigned_to,
        title=title,
        message=message,
        type="info",
        url=f"/tasks/{task.pk}/",
    )



def create_admin_review_task_for_completed_task(task, actor):
    if task.child_tasks.exists():
        return None


    control_type = TaskType.objects.filter(
        name__iexact="Controle",
        is_active=True,
    ).first()

    open_status = Status.objects.filter(
        scope="task",
        name__iexact="Open",
        is_active=True,
    ).first()

    admin_user = User.objects.filter(
        is_superuser=True,
        is_active=True,
    ).order_by("id").first()

    if not control_type or not open_status or not admin_user:
        return None

    review_task = Task.objects.create(
        parent_task=task,
        type=control_type,
        status=open_status,
        assigned_to=admin_user,
        assigned_by=actor,
        signal=task.signal,
        due_at=task.due_at,
        body=(
            f"Controleer of taak #{task.id} correct is afgerond.\n\n"
            f"Originele taakomschrijving:\n{task.body or '-'}"
        ),
    )

    if task.people.exists():
        review_task.people.set(task.people.all())

    return review_task