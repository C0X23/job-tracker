import markdown2
from django import template
from django.utils.safestring import SafeString, mark_safe

from applications.views import STATUS_COLORS

register = template.Library()

_MARKDOWN_EXTRAS = ["fenced-code-blocks", "tables", "break-on-newline", "strike"]


@register.filter
def status_color_filter(status: str) -> str:
    return STATUS_COLORS.get(status, "bg-gray-100 text-gray-700")


@register.filter(name="markdown")
def markdown_filter(value: str | None) -> SafeString:
    if not value:
        return mark_safe("")
    html = markdown2.markdown(value, extras=_MARKDOWN_EXTRAS, safe_mode="escape")
    return mark_safe(html)
