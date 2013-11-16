# coding: utf-8

# PYTHON IMPORTS
import time
import datetime
from functools import update_wrapper, partial

# DJANGO IMPORTS
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from django.contrib.admin.helpers import AdminForm
from django import forms
from django.forms.formsets import all_valid
from django.utils.html import escape
from django.utils import six
from django.db.models.loading import get_model
from django.utils.text import get_text_list
from django.contrib.admin.util import flatten_fieldsets
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.db.models import Q

# PROJECT IMPORTS
from vola.models import Language, Category, Container, Group, Plugin, Permission
from vola import signals


class AdminErrorList(forms.util.ErrorList):
    """
    Stores all errors for the form/formsets in an add/change stage view.
    """
    def __init__(self, form, inline_formsets):
        if form.is_bound:
            self.extend(list(six.itervalues(form.errors)))
            for inline_formset in inline_formsets:
                self.extend(inline_formset.non_form_errors())
                for errors_in_inline_form in inline_formset.errors:
                    self.extend(list(six.itervalues(errors_in_inline_form)))


class LanguageAdmin(admin.ModelAdmin):

    list_display = ("name", "position",)
    list_display_links = ("name",)
    list_filter = ("create_date", "update_date",)
    list_editable = ("position",)

admin.site.register(Language, LanguageAdmin)


class CategoryAdmin(admin.ModelAdmin):

    list_display = ("name", "position",)
    list_display_links = ("name",)
    list_filter = ("create_date", "update_date",)
    list_editable = ("position",)

admin.site.register(Category, CategoryAdmin)


class PermissionInline(admin.StackedInline):

    model = Permission
    classes = ('grp-collapse grp-open',)
    fields = ("user", "group", "manage_container", "manage_preview", "manage_plugins",)
    extra = 1


class GroupInline(admin.StackedInline):

    model = Group
    classes = ('grp-collapse grp-open',)
    sortable_field_name = "position"
    sortable_excludes = ("menu",)
    fields = ("name", "slug", "menu", "plugins_include", "plugins_exclude", "position",)
    extra = 1


class PluginAdmin(admin.ModelAdmin):
    """
    Plugins admin models need to extend this base class
    """
    change_form_template = "admin/vola/container/plugin.html"
    inline_classes_change = ("grp-collapse grp-closed",)
    inline_classes_add = ("grp-collapse grp-open",)

    # fieldsets, if no fields/fieldsets are defined with the subclass
    fieldsets = (
        ("", {
            "fields": ("position",),
        }),
    )
    # additional fields for managers/superusers
    manager_fieldsets = (
        (_("Manage Plugin"), {
            "classes": ("grp-collapse grp-open",),
            "fields": ("lock_content", "lock_position",),
        }),
    )

    # def get_fieldsets(self, request, obj=None):
    #     fieldsets = super(PluginAdmin, self).get_fieldsets(request, obj)
    #     if request.user.is_superuser:
    #         return list(self.manager_fieldsets) + list(fieldsets)
    #     return list(fieldsets)

    def get_form(self, request, obj=None, **kwargs):
        """
        Workaround bug http://code.djangoproject.com/ticket/9360 (thanks to peritus)
        """
        return super(PluginAdmin, self).get_form(request, obj, fields=flatten_fieldsets(self.get_fieldsets(request, obj)))

    # @csrf_protect_m
    # @transaction.commit_on_success
    def add_view(self, request, form_url="", extra_context=None):
        """
        Custom add view without inlines/formsets
        """
        model = self.model
        opts = model._meta

        # FIXME: return 404 if request is non-ajax

        if not self.has_add_permission(request):
            raise PermissionDenied

        c = request.GET.get("c", 1)
        s = request.GET.get("s")
        group = Group.objects.get(pk=s)
        prefix = "plugin_%s" % c

        ModelForm = self.get_form(request)
        form = ModelForm(prefix=prefix)

        adminForm = AdminForm(form, list(self.get_fieldsets(request)),
            self.get_prepopulated_fields(request),
            self.get_readonly_fields(request),
            model_admin=self)

        adminForm.original = False
        adminForm.can_delete = False
        adminForm.sortable_field_name = "position"
        adminForm.verbose_name = self.model._meta.verbose_name
        adminForm.original = None
        adminForm.prefix = prefix
        adminForm.app_label = self.model._meta.app_label
        adminForm.model_name = self.model.__name__.lower() # FIXME: ModelBase ???
        adminForm.inline_classes = adminForm.model_admin.inline_classes_add

        context = {
            "adminform": adminForm,
            "pluginmedia": self.media,
            "errors": AdminErrorList(form, []),
            "app_label": opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url, add=True)


class ContainerAdmin(admin.ModelAdmin):
    """
    Admin definition of Container
    """
    actions = None
    list_display = ("category", "container_name", "container_languages", "preview", "transfer_container", "transfer_date", "container_settings",)
    list_display_links = ("container_name",)
    list_filter = ("create_date", "update_date", "category", "preview",)
    search_fields = ("name",)

    fieldsets = (
        (_("General"), {
            "classes": ("grp-collapse grp-open",),
            "fields": ("name", "slug", "category",)
        }),
        (_("URL"), {
            "classes": ("grp-collapse grp-open",),
            "fields": ("page_url", "preview_url",),
        }),
        (_("Transfer"), {
            "classes": ("grp-collapse grp-open",),
            "fields": ("transfer_date",),
        }),
    )
    # transfer_date does not make sense for adding a
    # container, since it is only useful with previews
    fieldsets_add = (
        (_("General"), {
            "classes": ("grp-collapse grp-open",),
            "fields": ("name", "slug", "category",)
        }),
        (_("URL"), {
            "classes": ("grp-collapse grp-open",),
            "fields": ("page_url", "preview_url",),
        }),
    )
    inlines = [PermissionInline, GroupInline]
    prepopulated_fields = {"slug": ("name",)}

    # restricted
    restricted_list_display = ("category", "container_name", "container_languages", "preview", "transfer_container", "transfer_date",)
    restricted_fieldsets = (
        ("", {
            "fields": ("name", "transfer_date",)
        }),
    )

    def container_name(self, obj):
        """
        Always link to the first plugin section
        """
        if Language.objects.all().count():
            lang = Language.objects.all()[0]
            return "<a href='%d/group/%d/?lang=%s' class='vola-container-name'>%s</a>" % (obj.id, obj.groups.all()[0].id, lang, obj.name)
        else:
            return "<a href='%d/group/%d/' class='vola-container-name'>%s</a>" % (obj.id, obj.groups.all()[0].id, obj.name)
    container_name.short_description = _("Name")
    container_name.allow_tags = True
    container_name.admin_order_field = "name"

    def container_languages(self, obj):
        """
        Always link to languages
        """
        r = ''
        for item in Language.objects.all():
            r = r + "<a href='%d/group/%d/%s/' class='vola-container-language'>%s</a>" % (obj.id, obj.groups.all()[0].id, item, item)
        return r
    container_languages.short_description = _("Languages")
    container_languages.allow_tags = True

    def container_settings(self, obj):
        """
        Additional column linked with Container Settings
        """
        return "<a href='%d/' class='vola-container-settings'>%s</a>" % (obj.id, _("Settings"))
    container_settings.short_description = _("Settings")
    container_settings.allow_tags = True

    def queryset(self, request):
        """
        Show only Containers a user is assigned to with the changelist
        """
        qs = super(ContainerAdmin, self).queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(Q(permissions__user=request.user) | Q(permissions__group__user=request.user)).distinct()

    def get_list_display(self, request, obj=None):
        """
        Either all Columns or a restricted set.
        """
        if self.has_container_permission(request, obj):
            return self.list_display
        return self.restricted_list_display

    def get_fieldsets(self, request, obj=None):
        """
        Either all Container fields/inlines or just the preview fields (name, transfer_date).
        """
        if self.has_container_permission(request, obj):
            if obj:
                return super(ContainerAdmin, self).get_fieldsets(request, obj)
            return self.fieldsets_add
        return self.restricted_fieldsets

    def get_prepopulated_fields(self, request, obj=None):
        """
        No prepulated fields with preview
        """
        if obj and obj.preview:
            return {}
        return self.prepopulated_fields

    def get_form(self, request, obj=None, **kwargs):
        """
        Workaround bug http://code.djangoproject.com/ticket/9360
        """
        return super(ContainerAdmin, self).get_form(request, obj, fields=flatten_fieldsets(self.get_fieldsets(request, obj)))

    def get_urls(self):
        """
        Additional urls for previews and groups
        """
        from django.conf.urls import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name

        urlpatterns = patterns("",
            url(r"^$", wrap(self.changelist_view), name="%s_%s_changelist" % info),
            url(r"^add/$", wrap(self.add_view), name="%s_%s_add" % info),
            url(r"^(.+)/history/$", wrap(self.history_view), name="%s_%s_history" % info),
            url(r"^(.+)/delete/$", wrap(self.delete_view), name="%s_%s_delete" % info),
            url(r"^(?P<object_id>\d+)/group/(?P<group_id>\d+)/$", wrap(self.group_view), name="%s_%s_group" % info),
            url(r"^(.+)/make-preview/$", wrap(self.make_preview), name="%s_%s_make_preview" % info),
            url(r"^(.+)/transfer-preview/$", wrap(self.transfer_preview), name="%s_%s_transfer_preview" % info),
            url(r"^(.+)/$", wrap(self.change_view), name="%s_%s_change" % info),
        )
        return urlpatterns

    def get_available_plugins(self, group):
        """
        If registered plugin extends ``PluginAdmin``, append to plugin-list
        """
        plugins = []
        for model, model_admin in six.iteritems(self.admin_site._registry):
            if model_admin.__class__.__bases__[0].__name__ == "PluginAdmin":
                name = model._meta.verbose_name
                app_label = model._meta.app_label
                model_name = model.__name__.lower()
                plugin = "%s.%s" % (app_label, model_name)
                plugin_wildcard = "%s.*" % (app_label)
                # make sure we have the plugin if plugins_include and 
                # plugins_exclude is empty
                plugins.append({
                    "name": name,
                    "app_label": app_label,
                    "model_name": model_name
                })
                # remove plugin if it is not included
                if group.plugins_include != "" and \
                    not plugin in group.plugins_include.splitlines() and \
                    not plugin_wildcard in group.plugins_include.splitlines():
                    plugins.pop()
                # remove plugin if it is excluded
                if group.plugins_exclude != "" and \
                    plugin in group.plugins_exclude.splitlines() or \
                    plugin_wildcard in group.plugins_exclude.splitlines():
                    plugins.pop()
        plugins = sorted(plugins, key=lambda k: k["name"]) 
        return plugins

    def get_plugin_objects(self, request, app_label, model_name):
        """
        Return model, modeladmin and form for a plugin
        """
        model = get_model(app_label, model_name)
        modeladmin = self.admin_site._registry[model]
        modelform = modeladmin.get_form(request)
        return model, modeladmin, modelform

    def get_plugin_admin_form(self, request, prefix, model, modeladmin, form, group=None, obj=None):
        """
        Returns a single admin form for a given container plugin
        """
        #readonly_fields = modeladmin.get_readonly_fields(request)
        readonly_fields = modeladmin.get_readonly_fields(request, obj)
        af = AdminForm(form,
            list(modeladmin.get_fieldsets(request, obj)),
            modeladmin.get_prepopulated_fields(request, obj),
            readonly_fields,
            model_admin=modeladmin)
        af.prefix = prefix
        af.original = obj
        af.group = group
        af.can_delete = True
        af.sortable_field_name = "position"
        af.app_label = model._meta.app_label
        af.model_name = model.__name__.lower()
        af.verbose_name = model._meta.verbose_name
        af.inline_classes = modeladmin.inline_classes_change
        af.delete = request.POST.get("%s-DELETE" % prefix, 0)
        af.adminmedia = modeladmin.media # important for ajax calls
        return af

    def save_plugins(self, request, forms):
        for form in forms:
            delete = request.POST.get("%s-DELETE" % form.prefix, 0)
            if delete == "1":
                form.instance.delete()
            else:
                form.save()

    def save_extra_plugins(self, request, forms, obj, group):
        for form in forms:
            plugin = form.save(commit=False)
            plugin.container = obj
            plugin.group = group
            plugin.save()

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Additional permissions with the change view
        """
        obj = self.get_object(request, unquote(object_id))
        if not self.has_container_permission(request, obj) and not self.has_preview_permission(request, obj):
            raise PermissionDenied
        groups = Group.objects.filter(container=obj, menu=True)
        groups_additional = Group.objects.filter(container=obj, menu=False)
        extra_context = extra_context or {}
        extra_context["languages"] = Language.objects.all()
        extra_context["groups"] = groups
        extra_context["groups_additional"] = groups_additional
        extra_context["has_container_permission"] = self.has_container_permission(request, object_id)
        extra_context["has_preview_permission"] = self.has_preview_permission(request, object_id)
        extra_context["has_plugins_permission"] = self.has_plugins_permission(request, object_id)
        if self.has_preview_permission(request, obj) and not self.has_container_permission(request, obj):
            extra_context["inline_admin_formsets"] = []
        return super(ContainerAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def history_view(self, request, object_id, extra_context=None):
        return super(ContainerAdmin, self).history_view(request, object_id, extra_context=extra_context)

    # @csrf_protect_m
    # @transaction.commit_on_success
    def group_view(self, request, object_id, group_id, form_url="", extra_context=None):
        """
        The change form for a ``Group`` without inlines/formsets, extended with ``pluginforms``.
        """
        pluginforms = []
        pluginadminforms= []
        formsets = [] # no inlines with groups
        lang = request.GET.get("lang", None)
        if lang:
            language = Language.objects.get(name=lang)
        else:
            language = None

        extrapluginforms = []
        extrapluginadminforms = []
        extraforms_counter = 0
        
        model = self.model
        opts = model._meta
        media = self.media

        obj = self.get_object(request, unquote(object_id))
        # check permissions
        if not self.has_plugins_permission(request, obj):
            raise PermissionDenied
        # groups
        groups = Group.objects.filter(container=obj, menu=True)
        groups_additional = Group.objects.filter(container=obj, menu=False)
        group = Group.objects.get(pk=group_id) # FIXME: redirect if no group is given

        if obj is None:
            raise Http404(_("%(name)s object with primary key %(key)r does not exist.") % {"name": force_text(opts.verbose_name), "key": escape(object_id)})

        errors = False
        if request.method == "POST":
            # plugins
            counter = 0
            for i, item in enumerate(Plugin.objects.filter(group=group, container=obj, language=language), start=1):
                prefix = "plugin_%s" % i
                plugin = eval("item."+item.model_name)
                pluginModel, pluginModelAdmin, pluginModelForm = self.get_plugin_objects(request, item.app_label, item.model_name)
                pluginModelForm = pluginModelForm(request.POST, request.FILES, prefix=prefix, instance=plugin)
                pluginAdminForm = self.get_plugin_admin_form(request, prefix, pluginModel, pluginModelAdmin, pluginModelForm, group=group, obj=plugin)
                pluginadminforms.append(pluginAdminForm)
                pluginforms.append(pluginModelForm)
                media = media + pluginModelAdmin.media + pluginAdminForm.media
                counter = i
            # extra plugins
            extraforms_counter = int(request.POST.get("extraforms_counter", 0))
            if extraforms_counter > 0:
                for n in range(0, extraforms_counter):
                    prefix = "plugin_%s" % str(counter+1+n)
                    app_label = request.POST.get("%s-%s" % (prefix, "app_label"))
                    model_name = request.POST.get("%s-%s" % (prefix, "model_name"))
                    if app_label and model_name:
                        pluginModel, pluginModelAdmin, pluginModelForm = self.get_plugin_objects(request, app_label, model_name)
                        pluginModelForm = pluginModelForm(request.POST, request.FILES, prefix=prefix)
                        pluginAdminForm = self.get_plugin_admin_form(request, prefix, pluginModel, pluginModelAdmin, pluginModelForm, group=group)
                        pluginadminforms.append(pluginAdminForm)
                        extrapluginforms.append(pluginModelForm)
                        media = media + pluginModelAdmin.media + pluginAdminForm.media
            # save
            if all_valid(pluginforms) and all_valid(extrapluginforms):
                self.save_plugins(request, pluginforms)
                self.save_extra_plugins(request, extrapluginforms, obj, group)
                change_message = self.construct_plugin_message(request, pluginforms, extrapluginforms)
                self.log_change(request, obj, change_message)
                return self.response_change(request, obj)
            else:
                errors = True
        else:
            for i, item in enumerate(Plugin.objects.filter(group=group, container=obj, language=language), start=1):
                prefix = "plugin_%s" % i
                plugin = eval("item."+item.model_name)
                pluginModel, pluginModelAdmin, pluginModelForm = self.get_plugin_objects(request, item.app_label, item.model_name)
                pluginModelForm = pluginModelForm(prefix=prefix, instance=plugin)
                pluginAdminForm = self.get_plugin_admin_form(request, prefix, pluginModel, pluginModelAdmin, pluginModelForm, group=group, obj=plugin)
                pluginadminforms.append(pluginAdminForm)
                media = media + pluginModelAdmin.media + pluginAdminForm.media

        context = {
            "title": u"%s — %s" % (obj, group),
            "object_id": obj.id,
            "original": obj,
            "languages": Language.objects.all(),
            "language": request.GET.get("lang", None),
            "group": group,
            "groups": groups,
            "groups_additional": groups_additional,
            "app_label": opts.app_label,
            "pluginadminforms": pluginadminforms,
            "plugins": self.get_available_plugins(group),
            "extraforms_counter": extraforms_counter,
            "media": media,
            "errors": errors,
        }
        return self.render_group_form(request, context, change=True, obj=obj, form_url=form_url)

    def render_group_form(self, request, context, add=False, change=False, form_url="", obj=None):
        """
        Render group form, removed some variables compared to render_change_form.
        """
        opts = self.model._meta
        app_label = opts.app_label
        context.update({
            "has_add_permission": self.has_add_permission(request),
            "has_change_permission": self.has_change_permission(request, obj),
            "has_delete_permission": self.has_delete_permission(request, obj),
            "has_container_permission": self.has_container_permission(request, obj),
            "has_preview_permission": self.has_preview_permission(request, obj),
            "has_plugins_permission": self.has_plugins_permission(request, obj),
            "has_file_field": True, # FIXME - this should check if form or formsets have a FileField,
            "opts": opts,
        })
        return TemplateResponse(request, "admin/vola/container/group.html", context, current_app=self.admin_site.name)

    def construct_plugin_message(self, request, pluginforms, extrapluginforms):
        """
        Construct a change message for the plugins.
        """
        change_message = []
        # existing plugins (change/delete)
        for form in pluginforms:
            delete = form.data.get("%s-DELETE" % form.prefix, "0")
            if delete != "0": # raw data, therefore "0" insteaf of 0
                change_message.append(_("Deleted %s (%s).") % (form._meta.model._meta.verbose_name, force_text(form.instance)))
            elif form.changed_data:
                change_message.append(_("%s (%s): Changed %s.") % (form._meta.model._meta.verbose_name, force_text(form.instance), get_text_list(form.changed_data, _("and"))))
        # extra plugins (add)
        for form in extrapluginforms:
            change_message.append(_("Added %s (%s).") % (form._meta.model._meta.verbose_name, force_text(form.instance)))
        # message
        change_message = " ".join(change_message)
        return change_message or _("No fields changed.")

    # @transaction.commit_on_success
    def make_preview(self, request, object_id, form_url="", extra_context=None):
        """
        Create preview (including permissions and groups/plugins)
        """
        model = self.model
        opts = model._meta
        container = Container.objects.get(id=unquote(object_id))
        # check permissions
        if not self.has_preview_permission(request, container):
            raise PermissionDenied
        # pre signal
        signals.vola_pre_create_preview.send(sender=request, container=container)
        # temporarily save given values
        name = container.name
        slug = container.slug
        cache_key = container.cache_key
        transfer_container_id = container.id 
        # new container
        container.pk = None
        now = datetime.datetime.now()
        container.name = "%s (%s)" % (container.name, time.time())
        container.slug = "%s_%s" % (container.slug, time.time())
        container.cache_key = "%s_%s" % (container.cache_key, time.time())
        container.preview = True
        container.save(initial_group=False)
        # set new name/slug/cache_key
        container.name = "%s (%s)" % (name, container.id)
        container.slug = "%s_%s" % (slug, container.id)
        container.cache_key = "%s_%s" % (cache_key, container.id)
        container.transfer_container_id = transfer_container_id
        container.save(initial_group=False)
        # new permissions
        for permission in Permission.objects.filter(container__id=unquote(object_id)):
            permission.pk = None
            permission.container = container
            permission.save()
        # new groups and new plugins
        for group in Group.objects.filter(container__id=unquote(object_id)):
            group_id = group.id
            group.pk = None
            group.container = container
            group.save()
            for plugin in Plugin.objects.filter(container__id=unquote(object_id), group=group_id):
                p = eval("plugin."+plugin.model_name)
                p.pk = None
                p.id = None
                p.container = container
                p.group = group
                p.save()
        # post signal
        signals.vola_post_create_preview.send(sender=request, container=container)
        # message and redirect
        msg_dict = {"name": force_text(opts.verbose_name), "obj": force_text(container)}
        msg = _("The %(obj)s was added successfully. You may edit it again below.") % msg_dict
        self.message_user(request, msg)
        post_url_continue = reverse("admin:%s_%s_change" % (opts.app_label, opts.module_name), args=(container.id,), current_app=self.admin_site.name)
        return HttpResponseRedirect(post_url_continue)

    # @transaction.commit_on_success
    def transfer_preview(self, request, object_id, form_url="", extra_context=None):
        """
        Transfer preview (including permissions and groups/plugins)
        """
        model = self.model
        opts = model._meta
        preview = Container.objects.get(id=unquote(object_id))
        container = preview.transfer_container
        # check permissions
        if not self.has_preview_permission(request, container):
            raise PermissionDenied
        # pre signal
        signals.vola_pre_transfer_preview.send(sender=request, container=preview)
        # delete permissions and groups/plugins
        Permission.objects.filter(container=container).delete()
        Plugin.objects.filter(container=container).delete()
        Group.objects.filter(container=container).delete()
        # transfer permissions
        for permission in Permission.objects.filter(container=preview):
            permission.pk = None
            permission.container = container
            permission.save()
        # transfer groups and plugins
        for group in Group.objects.filter(container=preview):
            group_id = group.id
            group.pk = None
            group.container = container
            group.save()
            for plugin in Plugin.objects.filter(container=preview, group=group_id):
                p = eval("plugin."+plugin.model_name)
                p.pk = None
                p.id = None
                p.container = container
                p.group = group
                p.save()
        # FIXME: reset preview attributes
        # FIXME: transfer_date???
        # delete preview
        preview.delete()
        # post signal
        signals.vola_post_transfer_preview.send(sender=request, container=container)
        # message and redirect
        msg_dict = {"name": force_text(opts.verbose_name), "obj": force_text(container)}
        msg = _("The %(obj)s was changed successfully. You may edit it again below.") % msg_dict
        self.message_user(request, msg)
        post_url_continue = reverse("admin:%s_%s_change" % (opts.app_label, opts.module_name), args=(container.id,), current_app=self.admin_site.name)
        return HttpResponseRedirect(post_url_continue)

    # FIXME:
    # add delete preview (no delete container permissions needed)

    def has_container_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.has_perm("vola.change_container"):
            if Permission.objects.filter(container=obj, user=request.user, manage_container=True).exists() or \
                Permission.objects.filter(container=obj, group__in=request.user.groups.all().values_list("id"), manage_container=True).exists():
                return True
        return False

    def has_preview_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.has_perm("vola.change_container"):
            if Permission.objects.filter(container=obj, user=request.user, manage_preview=True).exists() or \
                Permission.objects.filter(container=obj, group__in=request.user.groups.all().values_list("id"), manage_preview=True).exists():
                return True
        return False

    def has_plugins_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.has_perm("vola.change_container"):
            if Permission.objects.filter(container=obj, user=request.user, manage_plugins=True).exists() or \
                Permission.objects.filter(container=obj, group__in=request.user.groups.all().values_list("id"), manage_plugins=True).exists():
                return True
        return False

# Registering the container model with the main admin site
# You should unregister this model when using a custom admin site
admin.site.register(Container, ContainerAdmin)
