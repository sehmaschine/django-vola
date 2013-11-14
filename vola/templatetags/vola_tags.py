# coding: utf-8

# DJANGO IMPORTS
from django import template

register = template.Library()

# PROJECT IMPORTS
from vola.models import Container, Group, Plugin


@register.assignment_tag(takes_context=True)
def vola_rendered_plugin_list(context, container_slug, group_slug):
    """
    Returns a list of rendered plugins

    Usage:
    {% vola_rendered_plugin_list "container_slug" "group_slug" as var %}
    """
    
    result_list = []
    slug = context["request"].GET.get(container_slug, container_slug) # preview
    plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug)

    for item in plugin_list:
        plugin = eval("item."+item.model_name)
        result_list.append(plugin.render(context))

    return result_list


@register.assignment_tag(takes_context=True)
def vola_plugin_list(context, container_slug, group_slug):
    """
    Returns a list of plugins as an object

    Usage:
    {% vola_plugin_list "container_slug" "group_slug" as var %}
    """
    
    result_list = []
    slug = context["request"].GET.get(container_slug, container_slug) # preview
    plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug)

    for item in plugin_list:
        plugin = eval("item."+item.model_name)
        result_list.append(plugin)

    return result_list


@register.assignment_tag(takes_context=True)
def vola_rendered_plugin(context, container_slug, group_slug, plugin_slug):
    """
    Returns a single rendered plugins

    Usage:
    {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" as var %}
    """
    
    slug = context["request"].GET.get(container_slug, container_slug) # preview
    plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug)

    for item in plugin_list:
        plugin = eval("item."+item.model_name)
        if plugin.slug == plugin_slug:
            return plugin.render(context)

    return None


@register.assignment_tag(takes_context=True)
def vola_plugin(context, container_slug, group_slug, plugin_slug):
    """
    Returns a single plugin as an object

    Usage:
    {% vola_plugin "container_slug" "group_slug" "plugin_slug" as var %}
    """
    
    slug = context["request"].GET.get(container_slug, container_slug) # preview
    plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug)

    for item in plugin_list:
        plugin = eval("item."+item.model_name)
        if plugin.slug == plugin_slug:
            return plugin

    return None

