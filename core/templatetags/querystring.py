from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def qs_set(context, **kwargs):
    request = context["request"]
    qd = request.GET.copy()

    for k, v in kwargs.items():
        if v is None or v == "":
            qd.pop(k, None)
        else:
            qd[k] = str(v)

    return qd.urlencode()