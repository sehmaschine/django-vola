# coding: utf-8

# DJANGO IMPORTS
from django import template

register = template.Library()

# PROJECT IMPORTS
from vola.models import Language, Category, Container, Group, Plugin


@register.assignment_tag(takes_context=True)
def vola_plugin_list(context, container_slug, group_slug, *args, **kwargs):
    """
    Returns a list of plugins

    Usage:
    {% vola_get_plugin_list "container_slug" "group_slug" as var %}
    {% vola_get_plugin_list "container_slug" "group_slug" language="de" as var %}

    FIXME: displaying pluginlist with template throws error
    """
    
    result_list = []
    slug = context["request"].GET.get(container_slug, container_slug) # preview
    language = kwargs.get("language", None)
    plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

    for item in plugin_list:
        plugin = eval("item."+item.model_name)
        result_list.append(plugin)
    return result_list


@register.assignment_tag(takes_context=True)
def vola_rendered_plugin_list(context, container_slug, group_slug, *args, **kwargs):
    """
    Returns a list of rendered plugins

    Usage:
    {% vola_rendered_plugin_list "container_slug" "group_slug" as var %}
    {% vola_rendered_plugin_list "container_slug" "group_slug" language="de" as var %}
    """
    
    result_list = []
    slug = context["request"].GET.get(container_slug, container_slug) # preview
    language = kwargs.get("language", None)
    plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

    for item in plugin_list:
        plugin = eval("item."+item.model_name)
        result_list.append(plugin.render(context, *args, **kwargs))
    return result_list


@register.assignment_tag(takes_context=True)
def vola_data_plugin_list(context, container_slug, group_slug, *args, **kwargs):
    """
    Returns a list of plugins with data

    Usage:
    {% vola_data_plugin_list "container_slug" "group_slug" as var %}
    {% vola_data_plugin_list "container_slug" "group_slug" language="de" as var %}
    """
    
    result_list = []
    slug = context["request"].GET.get(container_slug, container_slug) # preview
    language = kwargs.get("language", None)
    plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

    for item in plugin_list:
        plugin = eval("item."+item.model_name)
        result_list.append(plugin.data(context, *args, **kwargs))
    return result_list


@register.assignment_tag(takes_context=True)
def vola_plugin(context, container_slug, group_slug, plugin_slug, *args, **kwargs):
    """
    Returns a single plugin

    Usage:
    {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" as var %}
    {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" language="de" as var %}
    """
    
    slug = context["request"].GET.get(container_slug, container_slug) # preview
    language = kwargs.get("language", None)
    plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

    for item in plugin_list:
        plugin = eval("item."+item.model_name)
        if plugin.slug == plugin_slug:
            return plugin
    return None


@register.assignment_tag(takes_context=True)
def vola_rendered_plugin(context, container_slug, group_slug, plugin_slug, *args, **kwargs):
    """
    Returns a single rendered plugin

    Usage:
    {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" as var %}
    {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" language="de" as var %}
    """
    
    slug = context["request"].GET.get(container_slug, container_slug) # preview
    language = kwargs.get("language", None)
    plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

    for item in plugin_list:
        plugin = eval("item."+item.model_name)
        if plugin.slug == plugin_slug:
            return plugin.render(context, *args, **kwargs)
    return None


@register.assignment_tag(takes_context=True)
def vola_data_plugin(context, container_slug, group_slug, plugin_slug, *args, **kwargs):
    """
    Returns a single plugin as an object

    Usage:
    {% vola_data_plugin "container_slug" "group_slug" "plugin_slug" as var %}
    {% vola_data_plugin "container_slug" "group_slug" "plugin_slug" language="de" as var %}
    """
    
    slug = context["request"].GET.get(container_slug, container_slug) # preview
    language = kwargs.get("language", None)
    plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

    for item in plugin_list:
        plugin = eval("item."+item.model_name)
        if plugin.slug == plugin_slug:
            return plugin.data(context, *args, **kwargs)
    return None


@register.assignment_tag(takes_context=True)
def vola_data(context, plugin, *args, **kwargs):
    """
    Renders a plugin

    Usage:
    {% vola_data plugin %}
    """
    return plugin.data(context, *args, **kwargs)


@register.assignment_tag(takes_context=True)
def vola_render(context, plugin, *args, **kwargs):
    """
    Renders a plugin

    Usage:
    {% vola_render plugin %}
    """
    return plugin.render(context, *args, **kwargs)


class RenderAsTemplateNode(template.Node):
    def __init__(self, item_to_be_rendered):
        self.item_to_be_rendered = template.Variable(item_to_be_rendered)

    def render(self, context):
        try:
            actual_item = self.item_to_be_rendered.resolve(context)
            return template.Template(actual_item).render(context)
        except template.VariableDoesNotExist:
            return ''

def vola_render_as_template(parser, token):
    bits = token.split_contents()
    if len(bits) !=2:
        raise template.TemplateSyntaxError("'%s' takes only one argument (a variable representing a template to render)" % bits[0])    
    return RenderAsTemplateNode(bits[1])

vola_render_as_template = register.tag(vola_render_as_template)

