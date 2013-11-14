# coding: utf-8

# PYTHON IMPORTS
import datetime

# DJANGO IMPORTS
from django.db import models
from django import template
from django.db.models.signals import post_save
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.conf.global_settings import LANGUAGES
from django.contrib.auth.models import User, Group as UserGroup
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

# PROJECT IMPORTS
from positions.fields import PositionField
#from vola.cache import cache_callback


class Language(models.Model):
    """
    Languages for a ``Vola``
    """

    name = models.CharField(_("Name"), max_length=7, choices=LANGUAGES, unique=True)
    position = PositionField(_("Position"))

    # internal
    create_date = models.DateTimeField(_("Date (Create)"), auto_now_add=True)
    update_date = models.DateTimeField(_("Date (Update)"), auto_now=True)
    
    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")
        ordering = ["position"]

    def __str__(self):
        return "%s" % self.name

    def __unicode__(self):
        return u"%s" % self.name


class Category(models.Model):
    """
    Category for a ``Container``

    The ``Category`` separates different types of ``Containers``
    and it only affects the admin interface
    """

    name = models.CharField(_("Name"), max_length=200, unique=True)
    position = PositionField(_("Position"))

    # internal
    create_date = models.DateTimeField(_("Date (Create)"), auto_now_add=True)
    update_date = models.DateTimeField(_("Date (Update)"), auto_now=True)
    
    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["position"]

    def __str__(self):
        return "%s" % self.name

    def __unicode__(self):
        return u"%s" % self.name


class Container(models.Model):
    """
    The main ``Container`` model

    A ``Container`` is a wrapper for ``Groups`` and ``Plugins``.
    """
    
    name = models.CharField(_("Name"), max_length=200, unique=True)
    slug = models.SlugField(_("Slug"), max_length=200, unique=True)
    cache_key = models.SlugField(_("Cache Key"), max_length=200, unique=True) # not editable
    category = models.ForeignKey(Category, related_name="containers", blank=True, null=True)

    # preview/transfer
    preview = models.BooleanField(_("Preview")) # not editable
    preview_url = models.CharField(_("Preview URL"), max_length=200, blank=True)
    transfer_date = models.DateTimeField(_("Transfer Date"), blank=True, null=True)
    transfer_container = models.ForeignKey("self", verbose_name=_("Transfer Container"), related_name="previews", blank=True, null=True) # not editable

    # admin
    site = models.ForeignKey(Site, verbose_name=_("Site"), blank=True, null=True) # currently not used
    position = models.PositiveIntegerField(_("Position"), blank=True, null=True)
    
    # internal
    create_date = models.DateTimeField(_("Date (Create)"), auto_now_add=True)
    update_date = models.DateTimeField(_("Date (Update)"), auto_now=True)

    class Meta:
        verbose_name = _("Container")
        verbose_name_plural = _("Containers")
        ordering = ["name", "-preview"]

    def __str__(self):
        return "%s" % self.name

    def __unicode__(self):
        return u"%s" % self.name

    def save(self, *args, **kwargs):
        if self.slug: self.cache_key = self.slug
        super(Container, self).save(*args, **kwargs)
        if self.preview: self.transfer_container = self
        if not self.preview: self.transfer_date = self.transfer_container = None

# cache callback
# post_save.connect(cache_callback, sender=Container)

class Group(models.Model):
    """
    Group for a ``Container``

    A ``Group`` consists of associated ``Plugins``.

    With the admin interface, each ``Group`` within a ``Container`` is
    edited with a single page. If no ``Group`` is given, all ``Plugins``
    are directly linked with a ``Container``.
    """

    container = models.ForeignKey(Container, related_name="groups")
    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=200)
    cache_key = models.SlugField(_("Cache Key"), max_length=200) # not editable
    description = models.TextField(_("Description"), blank=True) # currently not used

    # plugins
    plugins_include = models.TextField(_("Plugins (Include)"), blank=True, help_text=_("List of app_label.model_name or app_label.* ... one entry per row."))
    plugins_exclude = models.TextField(_("Plugins (Exclude)"), blank=True, help_text=_("List of app_label.model_name or app_label.* ... one entry per row."))

    # admin
    menu = models.BooleanField(_("Menu"), default=1)
    position = models.PositiveIntegerField(_("Position"))

    # internal
    create_date = models.DateTimeField(_("Date (Create)"), auto_now_add=True)
    update_date = models.DateTimeField(_("Date (Update)"), auto_now=True)
    
    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ["-menu", "position"]
        unique_together = (("container", "slug"), ("container", "cache_key"),)
    
    def __str__(self):
        return "%s" % self.name

    def __unicode__(self):
        return u"%s" % self.name

    def save(self, *args, **kwargs):
        if self.slug: self.cache_key = self.slug
        super(Group, self).save(*args, **kwargs)

# cache callback
# post_save.connect(cache_callback, sender=Group)
    

class Plugin(models.Model):
    """
    Plugin for a ``Container``

    This model needs to be subclassed by a each plugin and
    the subclass must not contain fields already defined here.
    """
    
    container = models.ForeignKey(Container, related_name="plugins")
    group = models.ForeignKey(Group, related_name="plugins", blank=True, null=True)
    language = models.ForeignKey(Language, related_name="plugins", blank=True, null=True)

    # plugin meta information
    app_label = models.CharField(_("App Label"), max_length=100, blank=True)
    model_name = models.CharField(_("Model Name"), max_length=100, blank=True)

    # admin
    lock_content = models.BooleanField(_("Lock Content"))
    lock_position = models.BooleanField(_("Lock Position"))
    position = models.PositiveIntegerField(_("Position"))

    # internal
    create_date = models.DateTimeField(_("Date (Create)"), auto_now_add=True)
    update_date = models.DateTimeField(_("Date (Update)"), auto_now=True)
    
    class Meta:
        verbose_name = _("Plugin")
        verbose_name_plural = _("Plugins")
        ordering = ["position"]

    def __str__(self):
        return "%s" % self.id

    def __unicode__(self):
        return u"%s" % self.id

    @property
    def get_plugin(self):
        if self.model_name:
            return eval("self."+self.model_name)
        return None
    
    @property
    def template_name(self):
        """
        Default template name equals model_name,
        Override this with your custom plugin (if needed)
        """
        return self.model_name

    def get_template(self):
        """
        Loading template for a plugin
        """
        templates = [
            "containers/plugins/%s/%s.html" % (self.app_label, self.template_name),
            "plugins/%s/%s.html" % (self.app_label, self.template_name),
            "%s/%s.html" % (self.app_label, self.template_name),
            "%s.html" % (self.template_name),
        ]
        return template.loader.select_template(templates)

    def clean(self, *args, **kwargs):
        """
        If content is locked, all values derive from the existing object
        If position is locked and the plugin has been moved, we'll throw an error
        """
        instance = self.get_plugin
        if instance and instance.lock_content and self.lock_content:
            for f in self._meta.fields:
                # FIXME: improve these hardcoded values
                if f.name not in ["id", "plugin_ptr", "container", "group",\
                    "app_label", "model_name",\
                    "lock_content", "lock_position", "position",\
                    "create_date", "update_date"]:
                    setattr(self, f.attname, getattr(instance, f.attname))
        # FIXME: check for locked position, which could be hard when deleting rows:
        # if instance and instance.lock_position and instance.position != self.position:
        #     raise ValidationError()

    def save(self, *args, **kwargs):
        """
        Set ``app_label`` and ``model_name`` when saving a plugin
        """
        self.app_label = self._meta.app_label
        self.model_name = self.__class__.__name__.lower()
        super(Plugin, self).save(*args, **kwargs)

# cache callback
# post_save.connect(cache_callback, sender=Plugin)


class Permission(models.Model):
    """
    Permission model for Container.

    Manage the container
    --------------------
    This permission is needed in order to change container settings.
    Only assign this permission to an editor if you exactly know what you're doing.
    Usually, only superusers (or administrators) need this permission.
    
    Manage previews
    ---------------
    This permission is needed in order to create and transfer previews.
    You probably assign this permission to every editor who works with vola.
    
    Manage plugins
    --------------
    This permission is needed to lock/unlock the content and/or position of a plugin.
    Depending on your usecase, you may (or may not) assign these permissions to editors.
    Most probably, only superusers (or administrators) need this permission.
    """

    container = models.ForeignKey(Container, related_name="permissions")
    user = models.ForeignKey(User, null=True, blank=True, related_name='vola_permissions')
    group = models.ForeignKey(UserGroup, null=True, blank=True, related_name='vola_permissions')

    # permissions
    manage_container = models.BooleanField(_("Manage Container"))
    manage_preview = models.BooleanField(_("Manage Preview"))
    manage_plugins = models.BooleanField(_("Manage Plugins"))

    # internal
    create_date = models.DateTimeField(_("Date (Create)"), auto_now_add=True)
    update_date = models.DateTimeField(_("Date (Update)"), auto_now=True)

    def __str__(self):
        if self.user:
            return "%s" % self.user
        return "%s" % self.group

    def __unicode__(self):
        if self.user:
            return u"%s" % self.user
        return u"%s" % self.group

    class Meta:
        verbose_name = _('Permission')
        verbose_name_plural = _('Permissions')
        unique_together = ("container", "user", "group",)

    def save(self, *args, **kwargs):
        super(Permission, self).save(*args, **kwargs)

