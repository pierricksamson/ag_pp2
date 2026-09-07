"""Filtres de template pour les notes (couleurs Tailwind, %)."""

from django import template

register = template.Library()


def _color(value):
    if value is None:
        return "gray"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "gray"
    if v >= 14:
        return "green"
    if v >= 10:
        return "amber"
    return "red"


_BADGE = {
    "green": "bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200",
    "amber": "bg-amber-100 text-amber-800 ring-1 ring-amber-200",
    "red":   "bg-rose-100 text-rose-800 ring-1 ring-rose-200",
    "gray":  "bg-slate-100 text-slate-700 ring-1 ring-slate-200",
}
_TEXT = {
    "green": "text-emerald-600",
    "amber": "text-amber-600",
    "red":   "text-rose-600",
    "gray":  "text-slate-500",
}
_STATUS = {
    "PRESENT":       "bg-emerald-100 text-emerald-700",
    "ABSENT":        "bg-rose-100 text-rose-700",
    "DISPENSED":     "bg-slate-100 text-slate-700",
    "NOT_SUBMITTED": "bg-amber-100 text-amber-700",
}


@register.filter
def average_badge(value):
    return _BADGE[_color(value)]


@register.filter
def average_text_color(value):
    return _TEXT[_color(value)]


@register.filter
def status_class(value):
    return _STATUS.get(value, "bg-slate-100 text-slate-700")


@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return ""


@register.filter
def pct(value, total):
    try:
        if not total:
            return 0
        return round(100 * float(value) / float(total), 1)
    except (TypeError, ValueError):
        return 0