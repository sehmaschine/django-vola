# coding: utf-8

# DJANGO IMPORTS
from django.db import models

# VOLA IMPORTS
from vola.models import Plugin

# We define some models in order to use relations with vola.
# These models just show what _could_ be in your database.

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

# Now we define some vola plugins

class PluginSnippet(Plugin):
    u"""
    Simple text snippet
    """
    
    title = models.CharField("Title", max_length=200)
    slug = models.SlugField("Slug", max_length=200)
    body = models.TextField("Body")
    
    class Meta:
        verbose_name = "Snippet"
        verbose_name_plural = "Snippets"
    
    def __unicode__(self):
        return self.title

    def render(self, context=None):
        t = self.get_template()
        c = template.RequestContext(context["request"], {
            "title": self.title,
            "body": self.body,
        })
        return t.render(c)


class PluginBlogOverview(Plugin):
    u"""
    Latest Blog Entries
    """

    limit = models.PositiveIntegerField("Limit", blank=True, null=True)
    
    class Meta:
        verbose_name = "Latest Blog Entries"
        verbose_name_plural = "Latest Blog Entries"
    
    def __unicode__(self):
        return "Latest Blog Entries"

    def render(self, context=None):
        t = self.get_template()
        c = template.RequestContext(context["request"], {
            "title": self.title,
            "body": self.body,
        })
        return t.render(c)


class PluginBlogEntry(Plugin):
    u"""
    Single Blog Entry
    """

    blogentry = models.ForeignKey(BlogEntry)
    
    class Meta:
        verbose_name = "Single Blog Entry"
        verbose_name_plural = "Single Blog Entry"
    
    def __unicode__(self):
        return self.blogentry

    def render(self, context=None):
        t = self.get_template()
        c = template.RequestContext(context["request"], {
            "title": self.title,
            "body": self.body,
        })
        return t.render(c)


class PluginGeneric(Plugin):
    u"""
    Generic Content Object
    """

    blogentry = models.ForeignKey(BlogEntry)
    
    class Meta:
        verbose_name = "Generic Content Object"
        verbose_name_plural = "Generic Content Objects"
    
    def __unicode__(self):
        return self.blogentry

    def render(self, context=None):
        t = self.get_template()
        c = template.RequestContext(context["request"], {
            "title": self.title,
            "body": self.body,
        })
        return t.render(c)

