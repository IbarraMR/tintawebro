from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiplica dos valores numéricos."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
