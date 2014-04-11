# coding: utf-8

# PYTHON IMPORTS
import random
import hashlib

# DJANGO IMPORTS
from django.template import Library, Node, Template, TemplateSyntaxError, Variable, VariableDoesNotExist
from django.template import resolve_variable
from django.core.cache import cache
from django.utils.http import urlquote

register = Library()

# PROJECT IMPORTS
from vola.models import Language, Category, Container, Group, Plugin


def get_cache_key(category, container_slug, group_slug, plugin_slug=None, **kwargs):
    """
    The vola hierarchical cache key is constructed around containers & groups.
    Invalidation works with a post-save signal (cache callback) by
    incrementing the group-key (<container_slug>-<group_slug>).
    """
    # first, we try to retrieve the cache_group
    cache_group_key = "%s-%s" % (container_slug, group_slug)
    cache_group = cache.get(cache_group_key)
    # if the group has not been generated or is invalid,
    # we create the cache_group
    if cache_group is None:
        cache_group = random.randint(0, 10000)
        cache.set(cache_group_key, cache_group)
    # order the keyword arguments, because otherwise we will
    # build multiple caching instances (which is pointless)
    arguments = []
    for k in sorted(kwargs):
        arguments.append(kwargs.get(k, None))
    arguments = ":".join(arguments)
    # finally, build the cache key
    return "%s:%s:%s:%s" % (cache_group, category, plugin_slug, arguments)


@register.assignment_tag(takes_context=True)
def vola_plugin_list(context, container_slug, group_slug, *args, **kwargs):
    """
    Returns a list of plugins

    Usage:
    {% vola_plugin_list "container_slug" "group_slug" as var %}
    {% vola_plugin_list "container_slug" "group_slug" language="de" as var %}

    Optional keyword arguments:
    language
    """
    cache_key = get_cache_key("volapluginlist", container_slug, group_slug, **kwargs)
    result_list = cache.get(cache_key, None)

    if not result_list:
        result_list = []
        slug = context["request"].GET.get(container_slug, container_slug) # preview
        language = kwargs.get("language", None)
        plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

        for item in plugin_list:
            plugin = eval("item."+item.model_name)
            result_list.append(plugin)

        if cache_key:
            cache.set(cache_key, result_list)

    return result_list


@register.assignment_tag(takes_context=True)
def vola_rendered_plugin_list(context, container_slug, group_slug, *args, **kwargs):
    """
    Returns a list of rendered plugins

    For each plugin, the ``render`` method is being called which 
    usually results in an HTML template being rendered with a given context.

    Usage:
    {% vola_rendered_plugin_list "container_slug" "group_slug" as var %}
    {% vola_rendered_plugin_list "container_slug" "group_slug" language="de" as var %}

    Optional keyword arguments:
    template_prefix, template_suffix, language
    """
    cache_key = get_cache_key("volarenderedpluginlist", container_slug, group_slug, **kwargs)
    result_list = cache.get(cache_key, None)

    if not result_list:
        result_list = []
        slug = context["request"].GET.get(container_slug, container_slug) # preview
        language = kwargs.get("language", None)
        plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

        for item in plugin_list:
            plugin = eval("item."+item.model_name)
            result_list.append(plugin.render(context, *args, **kwargs))

        if cache_key:
            cache.set(cache_key, result_list)

    return result_list


@register.assignment_tag(takes_context=True)
def vola_data_plugin_list(context, container_slug, group_slug, *args, **kwargs):
    """
    Returns a list of plugins with data

    For each plugin, the ``data`` method is being called which 
    usually results in a dictionary response.

    Usage:
    {% vola_data_plugin_list "container_slug" "group_slug" as var %}
    {% vola_data_plugin_list "container_slug" "group_slug" language="de" as var %}

    Optional keyword arguments:
    language
    """
    cache_key = get_cache_key("voladatapluginlist", container_slug, group_slug, **kwargs)
    result_list = cache.get(cache_key, None)
    
    if not result_list:
        result_list = []
        slug = context["request"].GET.get(container_slug, container_slug) # preview
        language = kwargs.get("language", None)
        plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

        for item in plugin_list:
            plugin = eval("item."+item.model_name)
            result_list.append(plugin.data(context, *args, **kwargs))

        if cache_key:
            cache.set(cache_key, result_list)

    return result_list


@register.assignment_tag(takes_context=True)
def vola_plugin(context, container_slug, group_slug, plugin_slug, *args, **kwargs):
    """
    Returns a single plugin

    Usage:
    {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" as var %}
    {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" language="de" as var %}

    Optional keyword arguments:
    language
    """
    cache_key = get_cache_key("volaplugin", container_slug, group_slug, plugin_slug, **kwargs)
    result = cache.get(cache_key, None)
    
    if not result:
        slug = context["request"].GET.get(container_slug, container_slug) # preview
        language = kwargs.get("language", None)
        plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

        for item in plugin_list:
            plugin = eval("item."+item.model_name)
            if plugin.slug == plugin_slug:
                result = plugin

        if cache_key:
            cache.set(cache_key, result)

    return result


@register.assignment_tag(takes_context=True)
def vola_rendered_plugin(context, container_slug, group_slug, plugin_slug, *args, **kwargs):
    """
    Returns a single plugin using the plugins ``render`` method

    Usage:
    {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" as var %}
    {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" language="de" as var %}

    Optional keyword arguments:
    template_prefix, template_suffix, language
    """
    cache_key = get_cache_key("volarenderedplugin", container_slug, group_slug, plugin_slug, **kwargs)
    result = cache.get(cache_key, None)
    
    if not result:
        slug = context["request"].GET.get(container_slug, container_slug) # preview
        language = kwargs.get("language", None)
        plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

        for item in plugin_list:
            plugin = eval("item."+item.model_name)
            if plugin.slug == plugin_slug:
                result = plugin.render(context, *args, **kwargs)

        if cache_key:
            cache.set(cache_key, result)

    return result


@register.assignment_tag(takes_context=True)
def vola_data_plugin(context, container_slug, group_slug, plugin_slug, *args, **kwargs):
    """
    Returns a single plugin using the plugins ``data`` method

    Note that the single plugin can return a variety of types depending on
    your ``data`` method (dicts, lists, single objects).

    Usage:
    {% vola_data_plugin "container_slug" "group_slug" "plugin_slug" as var %}
    {% vola_data_plugin "container_slug" "group_slug" "plugin_slug" language="de" as var %}

    Optional keyword arguments:
    language
    """
    cache_key = get_cache_key("voladataplugin", container_slug, group_slug, plugin_slug, **kwargs)
    result = cache.get(cache_key, None)
    
    if not result:
        slug = context["request"].GET.get(container_slug, container_slug) # preview
        language = kwargs.get("language", None)
        plugin_list = Plugin.objects.filter(group__slug=group_slug, container__slug=slug, language__name=language)

        for item in plugin_list:
            plugin = eval("item."+item.model_name)
            if plugin.slug == plugin_slug:
                result = plugin.data(context, *args, **kwargs)

        if cache_key:
            cache.set(cache_key, result)

    return result


@register.assignment_tag(takes_context=True)
def vola_data(context, plugin, *args, **kwargs):
    """
    Returns the plugins data

    Useful in combination with ``vola_plugin`` in order to
    get a single plugins data.

    Usage:
    {% vola_data plugin %}
    """
    return plugin.data(context, *args, **kwargs)


@register.assignment_tag(takes_context=True)
def vola_render(context, plugin, *args, **kwargs):
    """
    Returns a rendered plugin

    Useful in combination with ``vola_plugin`` in order to
    actually render a single plugin.

    Usage:
    {% vola_render plugin %}

    Optional keyword arguments:
    template_prefix, template_suffix
    """
    return plugin.render(context, *args, **kwargs)


class RenderAsTemplateNode(Node):
    def __init__(self, item_to_be_rendered):
        self.item_to_be_rendered = Variable(item_to_be_rendered)

    def render(self, context):
        try:
            actual_item = self.item_to_be_rendered.resolve(context)
            return Template(actual_item).render(context)
        except VariableDoesNotExist:
            return ''

def vola_render_as_template(parser, token):
    bits = token.split_contents()
    if len(bits) !=2:
        raise TemplateSyntaxError("'%s' takes only one argument (a variable representing a template to render)" % bits[0])    
    return RenderAsTemplateNode(bits[1])

vola_render_as_template = register.tag(vola_render_as_template)

class CacheNode(Node):
    def __init__(self, nodelist, expire_time_var, fragment_name, container_slug, group_slug, vary_on):
        self.nodelist = nodelist
        self.expire_time_var = Variable(expire_time_var)
        self.fragment_name = fragment_name
        self.container_slug_var = Variable(container_slug)
        self.group_slug_var = Variable(group_slug)
        self.vary_on = vary_on

    def render(self, context):
        try:
            expire_time = self.expire_time_var.resolve(context)
        except VariableDoesNotExist:
            raise TemplateSyntaxError('"cache" tag got an unknown variable: %r' % self.expire_time_var.var)
        try:
            expire_time = int(expire_time)
        except (ValueError, TypeError):
            raise TemplateSyntaxError('"cache" tag got a non-integer timeout value: %r' % expire_time)
        # container slug (variable or string)
        try:
            container_slug = self.container_slug_var.resolve(context)
        except VariableDoesNotExist:
            raise TemplateSyntaxError('"cache" tag got an unknown variable: %r' % self.container_slug_var.var)
        # group slug (variable or string)
        try:
            group_slug = self.group_slug_var.resolve(context)
        except VariableDoesNotExist:
            raise TemplateSyntaxError('"cache" tag got an unknown variable: %r' % self.group_slug_var.var)
        # Build a unicode key for this fragment and all vary-on's.
        args = hashlib.md5(u':'.join([urlquote(resolve_variable(var, context)) for var in self.vary_on]))
        cache_key = get_cache_key("volatemplatecache.%s" % self.fragment_name, container_slug, group_slug, args.hexdigest())
        value = cache.get(cache_key)
        if value is None:
            value = self.nodelist.render(context)
            cache.set(cache_key, value, expire_time)
        return value

@register.tag('vola_cache')
def do_cache(parser, token):
    """
    This will cache the contents of a template fragment for a given amount
    of time.

    Usage::

        {% load cache %}
        {% cache [expire_time] [fragment_name] [cached_group_prefix] %}
            .. some expensive processing ..
        {% endcache %}

    This tag also supports varying by a list of arguments::

        {% load cache %}
        {% cache [expire_time] [fragment_name] [cached_group_prefix] [var1] [var2] .. %}
            .. some expensive processing ..
        {% endcache %}

    Each unique set of arguments will result in a unique cache entry.
    """
    nodelist = parser.parse(('endcache',))
    parser.delete_first_token()
    tokens = token.contents.split()
    if len(tokens) < 4:
        raise TemplateSyntaxError(u"'%r' tag requires at least 4 arguments." % tokens[0])
    return CacheNode(nodelist, tokens[1], tokens[2], tokens[3], tokens[4], tokens[5:])


