# coding: utf-8

# DJANGO IMPORTS
from django.db import models
from django import template
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.core.cache import cache

# VOLA IMPORTS
from vola.models import Plugin


# CACHE CALLBACK
def cache_callback(sender, **kwargs):
    """
    With the custom cache callback, you need to invalidate
    vola caches if related single objects are being saved.

    Even better, invalidate only if a plugin actually refers
    to the changed instance.
    """

    instance = kwargs.get("instance", None)

    # BlogEntry: PluginLatestBlogEntries, PluginBlogEntry
    if instance and isinstance(instance, BlogEntry):
        try:
            cache.incr("home-main")
        except:
            pass


# EXAMPLE MODELS
# We define some django models in order to use relations with vola.
# These models just show what _could_ be in your database.
# Take a look at plugins below in order to see how vola works based on these models.
# The models BlogEntry resp. CustomEntry are usually not part of
# your volaplugins.

class BlogEntry(models.Model):
    
    title = models.CharField("Title", max_length=200)
    pub_date = models.DateTimeField("Date")
    summary = models.TextField("Summary")
    body = models.TextField("Body", null=True)
    createdate = models.DateField("Date (Create)", auto_now_add=True)
    updatedate = models.DateField("Date (Update)", auto_now=True)
    
    class Meta:
        verbose_name = "Blog Entry"
        verbose_name_plural = "Blog Entries"
        ordering = ["-pub_date"]
    
    def __unicode__(self):
        return self.title
    
    @staticmethod
    def autocomplete_search_fields():
       return ("id__iexact", "title__icontains",)

# cache callback
# because the plugin PluginLatestBlogEntries refers to this model,
# we need to invalidate all cached groups with PluginLatestBlogEntries
# assigned (which is simply done by saving PluginLatestBlogEntries).
post_save.connect(cache_callback, sender=BlogEntry)


class CustomEntry(models.Model):
    
    title = models.CharField("Title", max_length=200)
    pub_date = models.DateTimeField("Date")
    summary = models.TextField("Summary")
    body = models.TextField("Body", null=True)
    createdate = models.DateField("Date (Create)", auto_now_add=True)
    updatedate = models.DateField("Date (Update)", auto_now=True)
    
    class Meta:
        verbose_name = "Custom Entry"
        verbose_name_plural = "Custom Entries"
        ordering = ["-pub_date"]
    
    def __unicode__(self):
        return self.title
    
    @staticmethod
    def autocomplete_search_fields():
       return ("id__iexact", "title__icontains",)

# EXAMPLE PLUGINS
# Now we define some plugins (some of them related to the models above).
# Usually, these plugins should go into "volaplugins".

class PluginSnippet(Plugin):
    """
    Simple text snippet

    Not related to any installed applications.
    """
    
    title = models.CharField("Title", max_length=200)
    body = models.TextField("Body")
    
    class Meta:
        verbose_name = "Snippet"
        verbose_name_plural = "Snippets"
    
    def __unicode__(self):
        return self.title

    def data(self, context=None, *args, **kwargs):
        return {
            "title": self.title,
            "body": self.body
        }

    def render(self, context=None, *args, **kwargs):
        t = self.get_template()
        c = template.RequestContext(context["request"], {
            "title": self.title,
            "body": self.body,
        })
        return t.render(c)


class PluginLatestBlogEntries(Plugin):
    """
    Latest Blog Entries

    Retrieving the latest blog entries, optionally with
    setting a limit variable.
    """

    limit = models.PositiveIntegerField("Limit", blank=True, null=True)
    
    class Meta:
        verbose_name = "Latest Blog Entries"
        verbose_name_plural = "Latest Blog Entries"
    
    def __unicode__(self):
        return "Latest Blog Entries"

    def data(self, context=None, *args, **kwargs):
        if self.limit:
            object_list = BlogEntry.objects.all()[:self.limit]
        else:
            object_list = BlogEntry.objects.all()[:10]
        return object_list

    def render(self, context=None, *args, **kwargs):
        object_list = self.data()
        t = self.get_template(context, *args, **kwargs)
        c = template.RequestContext(context["request"], {
            'object_list': object_list,
            'kwargs': kwargs
        })
        return t.render(c)


class PluginLatestCustomEntries(Plugin):
    """
    Latest Custom Entries

    Retrieving the latest custom entries, optionally with
    setting a limit variable.
    """

    limit = models.PositiveIntegerField("Limit", blank=True, null=True)
    
    class Meta:
        verbose_name = "Latest Custom Entries"
        verbose_name_plural = "Latest Custom Entries"
    
    def __unicode__(self):
        return "Latest Custom Entries"

    def data(self, context=None, *args, **kwargs):
        if self.limit:
            object_list = CustomEntry.objects.all()[:self.limit]
        else:
            object_list = CustomEntry.objects.all()[:10]
        return object_list

    def render(self, context=None, *args, **kwargs):
        object_list = self.data()
        t = self.get_template(context, *args, **kwargs)
        c = template.RequestContext(context["request"], {
            'object_list': object_list,
            'kwargs': kwargs
        })
        return t.render(c)


class PluginBlogEntry(Plugin):
    """
    Single Blog Entry

    Retrieving a single blog entry.
    """

    blogentry = models.ForeignKey(BlogEntry)
    
    class Meta:
        verbose_name = "Single Blog Entry"
        verbose_name_plural = "Single Blog Entry"
    
    def __unicode__(self):
        return self.blogentry

    def data(self, context=None, *args, **kwargs):
        return {
            "object": self.blogentry,
            "title": self.blogentry.title
        }

    def render(self, context=None, *args, **kwargs):
        t = self.get_template()
        c = template.RequestContext(context["request"], {
            "object": self.blogentry,
            "kwargs": kwargs,
        })
        return t.render(c)


class PluginCustomEntry(Plugin):
    """
    Single Custom Entry

    Retrieving a single blog entry.
    """

    customentry = models.ForeignKey(CustomEntry)
    
    class Meta:
        verbose_name = "Single Custom Entry"
        verbose_name_plural = "Single Custom Entry"
    
    def __unicode__(self):
        return self.customentry

    def data(self, context=None, *args, **kwargs):
        return {
            "object": self.customentry,
            "title": self.customentry.title
        }

    def render(self, context=None, *args, **kwargs):
        t = self.get_template()
        c = template.RequestContext(context["request"], {
            "object": self.customentry,
            "kwargs": kwargs,
        })
        return t.render(c)


class PluginGeneric(Plugin):
    """
    Generic Content by URL (object_id)

    Retrieving a single object based on content types.
    This example shows how you might define abstract,
    reusable plugins (though more descriptive plugins are
    probably better most of the time).
    """
    
    class Meta:
        verbose_name = "Generic Content Object"
        verbose_name_plural = "Generic Content Objects"
    
    def __unicode__(self):
        return u"Generic Content Object"

    def render(self, context=None):
        t = self.get_template()
        c = template.RequestContext(context["request"], {
            "title": self.title,
            "body": self.body,
        })
        return t.render(c)



