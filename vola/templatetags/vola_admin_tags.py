# coding: utf-8

# PYTHON IMPORTS
import re

# DJANGO IMPORTS
from django import template
from django.core.urlresolvers import reverse, get_callable

register = template.Library()

# PROJECT IMPORTS
from vola.models import Language, Category, Container, Group, Plugin


@register.assignment_tag(takes_context=True)
def vola_get_page_url(context):
    container = context["original"]
    language = context.get("language", None)
    url = re.sub("self.slug", container.slug, container.page_url)
    if language:
        url = re.sub("self.language", language.name, url)
    if container.page_url.startswith("reverse"):
        try:
            url = eval(url) # try reverse url, eval is EVIL!
        except:
            url = ""
    return url


@register.assignment_tag(takes_context=True)
def vola_get_preview_url(context):
    container = context["original"]
    language = context.get("language", None)
    url = re.sub("self.slug", container.slug, container.preview_url)
    if language:
        url = re.sub("self.language", language.name, url)
    if container.preview_url.startswith("reverse"):
        try:
            url = eval(url) # try reverse url, eval is EVIL!
        except:
            url = ""
    # add preview slug
    url += "?%s=%s" % (container.transfer_container.slug, container.slug)
    return url
