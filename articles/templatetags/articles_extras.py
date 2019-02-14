from django import template


register = template.Library()


def lookup(d, key):
    return d.get(key, '')


register.filter('lookup', lookup)

