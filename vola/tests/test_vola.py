# coding: utf-8

# PYTHON IMPORTS
import datetime

# DJANGO IMPORTS
from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType
from django import template
from django.core.cache import cache

# PROJECT IMPORTS
from vola.models import Language, Category, Container, Group, Plugin, Permission
from vola.templatetags.vola_tags import vola_plugin_list, vola_rendered_plugin_list, vola_data_plugin_list, vola_plugin, vola_rendered_plugin, vola_data_plugin, vola_data, vola_render, vola_render_as_template
from vola.templatetags.vola_tags import get_cache_key

# TEST IMPORTS
from vola.tests.models import BlogEntry, CustomEntry
from vola.tests.models import PluginSnippet, PluginLatestBlogEntries, PluginLatestCustomEntries, PluginBlogEntry, PluginCustomEntry, PluginGeneric


class VolalTestCase(TestCase):

    def _pre_setup(self):
        """
        Adding test models to INSTALLED APPS
        Set test cache backend
        """
        self.saved_INSTALLED_APPS = settings.INSTALLED_APPS
        self.saved_CACHES = settings.CACHES
        test_app = "vola.tests"
        settings.INSTALLED_APPS = tuple(
            list(self.saved_INSTALLED_APPS) + [test_app]
        )
        loading.load_app(test_app)
        call_command("syncdb", verbosity=0, interactive=False)
        # set custom cache backend
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "volatestcache"
            }
        }
        # FIXME: remove debug-toolbar from INSTALLED_APPS, because it
        # requires the standard cache library to be installed when rendering
        # templates (which is being done with the tests below)
        super(VolalTestCase, self)._pre_setup()

    def _post_teardown(self):
        """
        Reset INSTALLED APPS and CACHES
        """
        settings.INSTALLED_APPS = self.saved_INSTALLED_APPS
        settings.CACHES = self.saved_CACHES
        super(VolalTestCase, self)._post_teardown()
    
    def setUp(self):
        """
        The test case is based on three containers (home, blog, snippets).

        ├── Container Home
        │   ├── Group Main
        │   │   └── Plugins
        │   ├── Group Sidebar
        │   │   └── Plugins
        ├── Container Blog
        │   ├── Group Plugins
        │   │   └── Plugins
        └── Container Snippets
            └── Group Plugins
                └── Plugins
        """

        # client/factory
        self.client = Client()
        self.factory = RequestFactory()
        
        # users
        self.user_superuser = User.objects.create_superuser("superuser", "superuser@volaproject.com", "superuser")
        self.user_editor = User.objects.create_user("editor", "editor@volaproject.com", "editor")
        self.user_editor.is_staff = True
        self.user_editor.save()
        self.user_website = User.objects.create_user("user", "user@volaproject.com", "user")
        # languages
        self.language_en = Language.objects.create(id=1, name="en", position=0)
        self.language_de = Language.objects.create(id=2, name="de", position=1)
        # categories
        self.category_pages = Category.objects.create(id=1, name="Pages", position=0)
        self.category_snippets = Category.objects.create(id=2, name="Snippets", position=1)
        # containers (and 3 groups)
        self.container_page_home = Container.objects.create(id=1, name="Home", slug="home", category=self.category_pages)
        self.container_page_blog = Container.objects.create(id=2, name="Blog", slug="blog", category=self.category_pages)
        self.container_snippets = Container.objects.create(id=3, name="Snippets", slug="snippets", category=self.category_snippets)
        # groups (only for home)
        self.group_page_home_main = Group.objects.create(container=self.container_page_home, name="Main", slug="main", menu=True, position=1)
        self.group_page_home_sidebar = Group.objects.create(container=self.container_page_home, name="Sidebar", slug="sidebar", menu=True, position=2)
        self.group_page_blog = Group.objects.create(container=self.container_page_blog, name="Plugins", slug="plugins", menu=True, position=1)
        self.group_snippets = Group.objects.create(container=self.container_snippets, name="Plugins", slug="plugins", menu=True, position=1)

        # entries (100 blog entries and custom entries)
        for i in range(1,101):
            BlogEntry.objects.create(id=i,
                title=u"Blog Entry Nr. %s" % i,
                pub_date=datetime.date.today())
            CustomEntry.objects.create(id=i,
                title=u"Custom Entry Nr. %s" % i,
                pub_date=datetime.date.today())


class VolaBasicTests(VolalTestCase):
    
    def test_objects_created(self):
        """
        Test that objects have been created.
        """
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Language.objects.count(), 2)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(Container.objects.count(), 3)
        self.assertEqual(Group.objects.count(), 4)
        self.assertEqual(Plugin.objects.count(), 0)
        self.assertEqual(BlogEntry.objects.count(), 100)
        self.assertEqual(CustomEntry.objects.count(), 100)

    def test_urls(self):
        """
        Check URLs, no login
        """
        # login required
        # resonse 200, because we are redirected to the login page
        # ——————————
        # FIXME: how can we test this, because it is not a redirect???
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_add"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_delete", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_history", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_create_preview", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_group", args=[1,1]))
        self.assertEqual(response.status_code, 200)


class VolaPermissionTests(VolalTestCase):

    def test_login_superuser(self):
        """
        Test login, superuser
        """
        # login with superuser
        self.client.login(username="superuser", password="superuser")
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_add"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_delete", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_history", args=[1]))
        self.assertEqual(response.status_code, 200)
        # create preview redirects to the new preview container
        response = self.client.get(reverse("admin:vola_container_create_preview", args=[1]))
        self.assertRedirects(response, reverse("admin:vola_container_change", args=[4]), status_code=302, target_status_code=200)
        self.assertEqual(Container.objects.count(), 4)
        self.assertEqual(Group.objects.count(), 6) # two new groups with the preview
        # transfer preview redirects to the new preview container
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[4]))
        self.assertRedirects(response, reverse("admin:vola_container_change", args=[1]), status_code=302, target_status_code=200)
        self.assertEqual(Container.objects.count(), 3)
        self.assertEqual(Group.objects.count(), 4)
        # now we have groups with IDs 7 and 8
        # create_preview generates 5 and 6, transfer then generates 7 and 8
        response = self.client.get(reverse("admin:vola_container_group", args=[1,7]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_group", args=[1,8]))
        self.assertEqual(response.status_code, 200)
        # logout
        self.client.logout()

    def test_login_editor(self):
        """
        Test login, editor without permissions
        """
        # login with editor
        # no permissions are given, so response is always 403
        self.client.login(username="editor", password="editor")
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_add"))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_delete", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_history", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_create_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[1]))
        self.assertEqual(response.status_code, 403) # object does not exist
        response = self.client.get(reverse("admin:vola_container_group", args=[1,1]))
        self.assertEqual(response.status_code, 403)
        # logout
        self.client.logout()

    def test_login_editor_permissions_001(self):
        """
        Test login, editor with permissions

        General django container permissions only:
        can_change_container
        """
        content_type = ContentType.objects.get_for_model(Container)
        permission_1 = DjangoPermission.objects.get(content_type=content_type, codename='change_container')
        self.user_editor.user_permissions.add(permission_1)
        # can_change_container
        self.client.login(username="editor", password="editor")
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_add"))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_delete", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_history", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_create_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_group", args=[1,1]))
        self.assertEqual(response.status_code, 403)
        # logout
        self.client.logout()

    def test_login_editor_permissions_002(self):
        """
        Test login, editor with permissions

        General django container permissions only:
        can_change_container
        can_add_container
        """
        content_type = ContentType.objects.get_for_model(Container)
        permission_1 = DjangoPermission.objects.get(content_type=content_type, codename='change_container')
        permission_2 = DjangoPermission.objects.get(content_type=content_type, codename='add_container')
        self.user_editor.user_permissions.add(permission_1,permission_2)
        # can_change_container
        self.client.login(username="editor", password="editor")
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_add"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_delete", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_history", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_create_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_group", args=[1,1]))
        self.assertEqual(response.status_code, 403)
        # logout
        self.client.logout()

    def test_login_editor_permissions_003(self):
        """
        Test login, editor with permissions

        General django container permissions only:
        can_change_container
        can_add_container
        can_delete_container
        """
        content_type = ContentType.objects.get_for_model(Container)
        permission_1 = DjangoPermission.objects.get(content_type=content_type, codename='change_container')
        permission_2 = DjangoPermission.objects.get(content_type=content_type, codename='add_container')
        permission_3 = DjangoPermission.objects.get(content_type=content_type, codename='delete_container')
        self.user_editor.user_permissions.add(permission_1,permission_2,permission_3)
        # can_change_container
        self.client.login(username="editor", password="editor")
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_add"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        # 404, because of queryset restricted to permissions
        # missing row-level-permission
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("admin:vola_container_delete", args=[1]))
        # same as above
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("admin:vola_container_history", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_create_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_group", args=[1,1]))
        self.assertEqual(response.status_code, 403)
        # logout
        self.client.logout()

    def test_login_editor_permissions_003(self):
        """
        Test login, editor with permissions

        General django container permissions only:
        can_change_container
        manage_container
        """
        content_type = ContentType.objects.get_for_model(Container)
        permission_1 = DjangoPermission.objects.get(content_type=content_type, codename='change_container')
        self.user_editor.user_permissions.add(permission_1)
        Permission.objects.create(container_id=1, user=self.user_editor, manage_container=True)
        # can_change_container
        self.client.login(username="editor", password="editor")
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_add"))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_delete", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_history", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_create_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_group", args=[1,1]))
        self.assertEqual(response.status_code, 403) # FIXME: needs plugin permissions?
        # logout
        self.client.logout()

    def test_login_editor_permissions_003(self):
        """
        Test login, editor with permissions

        General django container permissions only:
        can_change_container
        manage_previews
        """
        content_type = ContentType.objects.get_for_model(Container)
        permission_1 = DjangoPermission.objects.get(content_type=content_type, codename='change_container')
        self.user_editor.user_permissions.add(permission_1)
        Permission.objects.create(container_id=1, user=self.user_editor, manage_preview=True)
        # can_change_container
        self.client.login(username="editor", password="editor")
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_add"))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_delete", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_history", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_create_preview", args=[1]), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[4]), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_group", args=[1,1]))
        self.assertEqual(response.status_code, 403) # FIXME: needs plugin permissions?
        # logout
        self.client.logout()

    def test_login_editor_permissions_003(self):
        """
        Test login, editor with permissions

        General django container permissions only:
        can_change_container
        manage_plugins
        """
        content_type = ContentType.objects.get_for_model(Container)
        permission_1 = DjangoPermission.objects.get(content_type=content_type, codename='change_container')
        self.user_editor.user_permissions.add(permission_1)
        Permission.objects.create(container_id=1, user=self.user_editor, manage_plugins=True)
        # can_change_container
        self.client.login(username="editor", password="editor")
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_add"))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_delete", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_history", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_create_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_group", args=[1,1]))
        self.assertEqual(response.status_code, 200) # FIXME: needs plugin permissions?
        # logout
        self.client.logout()


class VolaModelTests(VolalTestCase):
    
    def test_language_model(self):
        """
        Test language model
        """
        self.assertEqual(Language.objects.count(), 2)
        # required: name
        c = Category.objects.create(name="fr")
        self.assertEqual(c.position, 2)

    def test_category_model(self):
        """
        Test category model
        """
        self.assertEqual(Category.objects.count(), 2)
        # required: name
        c = Category.objects.create(name="Test")
        self.assertEqual(c.position, 2)

    def test_container_model(self):
        """
        Test container model
        """
        self.assertEqual(Container.objects.count(), 3)
        # required: name, slug
        c = Container.objects.create(name="Test", slug="test")
        self.assertEqual(Container.objects.count(), 4)
        # cache_key equals slug
        self.assertEqual(c.cache_key, "test")
        # preview
        c.preview = True
        c.transfer_date = datetime.datetime.now()
        c.save()
        self.assertEqual(c.transfer_container, c)
        # no preview
        c.preview = False
        c.save()
        self.assertEqual(c.transfer_date, None)
        self.assertEqual(c.transfer_container, None)

    def test_group_model(self):
        """
        Test group model
        """
        self.assertEqual(Group.objects.count(), 4)
        # required: name, slug
        g = Group.objects.create(container=self.container_page_home, name="Test", slug="test", position=2)
        self.assertEqual(Group.objects.count(), 5)
        # cache_key equals slug
        self.assertEqual(g.cache_key, "test")

    def test_plugin_model(self):
        """
        Test plugin model
        """
        self.assertEqual(Plugin.objects.count(), 0)
        # required: name, slug
        p = Plugin.objects.create(container=self.container_page_home, position=0)
        self.assertEqual(Plugin.objects.count(), 1)
        # app_label/model_name
        self.assertEqual(p.app_label, "vola")
        self.assertEqual(p.model_name, "plugin")
        # template_name
        self.assertEqual(p.template_name, "plugin")


class VolaViewTests(VolalTestCase):
    
    def test_container_changelist(self):
        """
        Test container changelist view
        """
        self.client.login(username="superuser", password="superuser")
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 200)
        # FIXME: check object_list count and columns

    def test_container_add(self):
        """
        Test add container
        """
        self.client.login(username="superuser", password="superuser")
        response = self.client.get(reverse("admin:vola_container_add"))
        self.assertEqual(response.status_code, 200)

    def test_container_edit(self):
        """
        Test edit container
        
        We only need to test extra_context, since everything else is
        a standard change_form with inlines
        """
        self.client.login(username="superuser", password="superuser")
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(response.status_code, 200)
        # 2 groups, no additional groups
        self.assertEqual(len(response.context["groups"]), 2)
        self.assertEqual(len(response.context["groups_additional"]), 0)
        # add additional group
        g = Group.objects.create(container=self.container_page_home, name="Test", slug="test", menu=False, position=2)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(len(response.context["groups"]), 2)
        self.assertEqual(len(response.context["groups_additional"]), 1)

    def test_container_delete(self):
        """
        Test delete container
        """
        pass

    def test_container_history(self):
        """
        Test container histrory
        """
        pass

    def test_container_create_preview(self):
        """
        Test create preview
        """
        pass

    def test_container_transfer_preview(self):
        """
        Test transfer preview
        """
        pass

    def test_group(self):
        """
        Test group within container
        """
        pass

    
class VolaTemplatetagTests(VolalTestCase):

    def test_vola_plugin_list(self):
        """
        Test templatetag ``vola_plugin_list``:

        Returns a list of plugin objects

        Usage:
        {% vola_plugin_list "container_slug" "group_slug" as var %}
        {% vola_plugin_list "container_slug" "group_slug" language="de" as var %}

        Optional keyword arguments:
        language
        """
        self.client.login(username="superuser", password="superuser")
        request = self.factory.get(reverse("admin:vola_container_changelist"))

        # testing with plugins returning a list of objects
        # [<PluginLatestBlogEntries: Latest Blog Entries>, <PluginLatestCustomEntries: Latest Custom Entries>]
        PluginLatestBlogEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, slug="blogentries", position=0, limit=2)
        PluginLatestCustomEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, slug="customentries", position=1, limit=2)
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_plugin_list "home" "main" as plugins %}
        {% for plugin in plugins %}<div class="plugin {{ plugin.slug }}">{{ plugin }}</div>{% endfor %}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="plugin blogentries">Latest Blog Entries</div><div class="plugin customentries">Latest Custom Entries</div>""")
        
        # we just get the plugins, so we can render it now
        # this is similar to vola_rendered_plugin_list below
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_plugin_list "home" "main" as plugins %}
        {% for plugin in plugins %}<div class="plugin {{ plugin.slug }}">{% vola_render plugin as content %}{{ content }}</div>{% endfor %}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="plugin blogentries"><div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div></div><div class="plugin customentries"><div class="obj">2014</div><div class="obj">2014</div></div>""")
        
        # we can also get the plugins data
        # this is similar to vola_data_plugin_list below
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_plugin_list "home" "main" as plugins %}
        {% for plugin in plugins %}<div class="plugin {{ plugin.slug }}">{% vola_data plugin as content %}{% for object in content %}<div class="obj">{{ object.title }}</div>{% endfor %}</div>{% endfor %}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="plugin blogentries"><div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div></div><div class="plugin customentries"><div class="obj">Custom Entry Nr. 1</div><div class="obj">Custom Entry Nr. 2</div></div>""")

        # check caching
        cache_key = get_cache_key("volapluginlist", "home", "main")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, [eval("item."+item.model_name) for item in Plugin.objects.filter(container__slug="home", group__slug="main")])
        # now add a plugin (this invalidates the cache_group)
        PluginSnippet.objects.create(container=self.container_page_home, group=self.group_page_home_main, position=2, title=u"snippet", body=u"xxx")
        # cache should now be empty
        cache_key = get_cache_key("volapluginlist", "home", "main")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, None)
        # using templatetag generates the new cache
        t = template.Template("""{% load vola_tags %}{% vola_plugin_list "home" "main" as plugins %}""")
        t.render(template.RequestContext(request, {}))
        # cache should be updated
        cache_key = get_cache_key("volapluginlist", "home", "main")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, [eval("item."+item.model_name) for item in Plugin.objects.filter(container__slug="home", group__slug="main")])

        # check caching with changing subitems
        # adding blog entry so it shows up first
        # PluginLatestBlogEntries = [<BlogEntry: Blog Entry Nr. 1000>, <BlogEntry: Blog Entry Nr. 1>]
        BlogEntry.objects.create(id=1000, title=u"Blog Entry Nr. 1000", pub_date=datetime.date.today()+datetime.timedelta(days=1))
        # we should now get the updated blog entry
        # vola_plugin_list only caches the plugins (not what´s inside the plugins),
        # so the new blog entry is already there without invalidating the cache
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_plugin_list "home" "main" as plugins %}
        {% for plugin in plugins %}<div class="plugin {{ plugin.slug }}">{% vola_render plugin as content %}{{ content }}</div>{% endfor %}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="plugin blogentries"><div class="obj">Blog Entry Nr. 1000</div><div class="obj">Blog Entry Nr. 1</div></div><div class="plugin customentries"><div class="obj">2014</div><div class="obj">2014</div></div><div class="plugin ">snippet</div>""")

    def test_vola_rendered_plugin_list(self):
        """
        Test templatetag ``vola_rendered_plugin_list``:

        Returns a list of rendered plugins

        Usage:
        {% vola_rendered_plugin_list "container_slug" "group_slug" as var %}
        {% vola_rendered_plugin_list "container_slug" "group_slug" language="de" as var %}

        Optional keyword arguments:
        template_prefix, template_suffix, language
        """
        self.client.login(username="superuser", password="superuser")
        request = self.factory.get(reverse("admin:vola_container_changelist"))

        # testing with a plugin which returns a list
        # so we are having a list of plugins, including a list
        # ob objects returned by the plugin
        # [u'<div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div>', u'<div class="obj">2014</div><div class="obj">2014</div>']
        PluginLatestBlogEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, position=0, limit=2)
        PluginLatestCustomEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, position=1, limit=2)
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_rendered_plugin_list "home" "main" as content %}
        {% for rendered_obj in content %}<div class="plugin">{{ rendered_obj }}</div>{% endfor %}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="plugin"><div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div></div><div class="plugin"><div class="obj">2014</div><div class="obj">2014</div></div>""")

        # testing with a plugin which returns an object
        # so we are having a list of plugins, including single objects
        # [u'<div class="obj">Blog Entry Nr. 1</div>', u'snippet']
        PluginBlogEntry.objects.create(container=self.container_page_blog, group=self.group_page_blog, position=0, blogentry_id=1)
        PluginSnippet.objects.create(container=self.container_page_blog, group=self.group_page_blog, position=1, title=u"snippet", body=u"xxx")
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_rendered_plugin_list "blog" "plugins" as content %}
        {% for rendered_obj in content %}<div class="plugin">{{ rendered_obj }}</div>{% endfor %}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="plugin"><div class="obj">Blog Entry Nr. 1</div></div><div class="plugin">snippet</div>""")

        # check caching
        cache_key = get_cache_key("volarenderedpluginlist", "home", "main")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, ['<div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div>', '<div class="obj">2014</div><div class="obj">2014</div>'])
        # now add a plugin (this invalidates the cache_group)
        PluginSnippet.objects.create(container=self.container_page_home, group=self.group_page_home_main, position=2, title=u"snippet", body=u"xxx")
        # cache should now be empty
        cache_key = get_cache_key("volarenderedpluginlist", "home", "main")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, None)
        # using templatetag generates the new cache
        t = template.Template("""{% load vola_tags %}{% vola_rendered_plugin_list "home" "main" as plugins %}""")
        t.render(template.RequestContext(request, {}))
        # cache should be updated
        cache_key = get_cache_key("volarenderedpluginlist", "home", "main")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, ['<div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div>', '<div class="obj">2014</div><div class="obj">2014</div>', 'snippet'])

        # check caching with changing subitems
        # adding blog entry so it shows up first
        BlogEntry.objects.create(id=1000, title=u"Blog Entry Nr. 1000", pub_date=datetime.date.today()+datetime.timedelta(days=1))
        # we should now get the updated blog entry
        # because of our custom cache callback
        t = template.Template("""{% load vola_tags %}{% vola_rendered_plugin_list "home" "main" as plugins %}""")
        t.render(template.RequestContext(request, {}))
        # cache should be updated
        cache_key = get_cache_key("volarenderedpluginlist", "home", "main")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, ['<div class="obj">Blog Entry Nr. 1000</div><div class="obj">Blog Entry Nr. 1</div>', '<div class="obj">2014</div><div class="obj">2014</div>', 'snippet'])

    def test_vola_data_plugin_list(self):
        """
        Test templatetag ``vola_data_plugin_list``:

        Returns a list of plugins with data

        Usage:
        {% vola_data_plugin_list "container_slug" "group_slug" as var %}
        {% vola_data_plugin_list "container_slug" "group_slug" language="de" as var %}

        Optional keyword arguments:
        language
        """
        self.client.login(username="superuser", password="superuser")
        request = self.factory.get(reverse("admin:vola_container_changelist"))

        # testing with a plugin which returns a list
        # so we are having a list of plugins, including a list
        # ob objects returned by the plugin
        # [[<BlogEntry: Blog Entry Nr. 1>, <BlogEntry: Blog Entry Nr. 2>], [<CustomEntry: Custom Entry Nr. 1>, <CustomEntry: Custom Entry Nr. 2>]]
        PluginLatestBlogEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, position=0, limit=2)
        PluginLatestCustomEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, position=1, limit=2)
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_data_plugin_list "home" "main" as content %}
        {% for plugin in content %}<div class="plugin">{% for obj in plugin %}<div class="obj">{{ obj.title }}</div>{% endfor %}</div>{% endfor %}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="plugin"><div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div></div><div class="plugin"><div class="obj">Custom Entry Nr. 1</div><div class="obj">Custom Entry Nr. 2</div></div>""")

        # testing with a plugin which returns an object
        # so we are having a list of plugins, including single objects
        # [{'object': <BlogEntry: Blog Entry Nr. 1>}, {'body': u'xxx', 'title': u'snippet'}]
        PluginBlogEntry.objects.create(container=self.container_page_blog, group=self.group_page_blog, position=0, blogentry_id=1)
        PluginSnippet.objects.create(container=self.container_page_blog, group=self.group_page_blog, position=1, title=u"snippet", body=u"xxx")
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_data_plugin_list "blog" "plugins" as content %}
        {% for object in content %}<div class="obj">{{ object.title }}</div>{% endfor %}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="obj">Blog Entry Nr. 1</div><div class="obj">snippet</div>""")

        # check caching
        cache_key = get_cache_key("voladatapluginlist", "home", "main")
        result_list = cache.get(cache_key, None)
        self.assertQuerysetEqual(result_list, ["[<BlogEntry: Blog Entry Nr. 1>, <BlogEntry: Blog Entry Nr. 2>]", "[<CustomEntry: Custom Entry Nr. 1>, <CustomEntry: Custom Entry Nr. 2>]"])
        # now add a plugin (this invalidates the cache_group)
        PluginSnippet.objects.create(container=self.container_page_home, group=self.group_page_home_main, position=2, title=u"snippet", body=u"xxx")
        # cache should now be empty
        cache_key = get_cache_key("voladatapluginlist", "home", "main")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, None)
        # using templatetag generates the new cache
        t = template.Template("""{% load vola_tags %}{% vola_data_plugin_list "home" "main" as content %}}""")
        t.render(template.RequestContext(request, {}))
        # cache should be updated
        cache_key = get_cache_key("voladatapluginlist", "home", "main")
        result_list = cache.get(cache_key, None)
        self.assertQuerysetEqual(result_list, ["[<BlogEntry: Blog Entry Nr. 1>, <BlogEntry: Blog Entry Nr. 2>]", "[<CustomEntry: Custom Entry Nr. 1>, <CustomEntry: Custom Entry Nr. 2>]", "{'body': u'xxx', 'title': u'snippet'}"])

        # check caching with changing subitems
        # adding blog entry so it shows up first
        BlogEntry.objects.create(id=1000, title=u"Blog Entry Nr. 1000", pub_date=datetime.date.today()+datetime.timedelta(days=1))
        # we should now get the updated blog entry
        # because of our custom cache callback
        t = template.Template("""{% load vola_tags %}{% vola_data_plugin_list "home" "main" as content %}""")
        t.render(template.RequestContext(request, {}))
        # cache should be updated
        cache_key = get_cache_key("voladatapluginlist", "home", "main")
        result_list = cache.get(cache_key, None)
        self.assertQuerysetEqual(result_list, ["[<BlogEntry: Blog Entry Nr. 1000>, <BlogEntry: Blog Entry Nr. 1>]", "[<CustomEntry: Custom Entry Nr. 1>, <CustomEntry: Custom Entry Nr. 2>]", "{'body': u'xxx', 'title': u'snippet'}"])

    def test_vola_plugin(self):
        """
        Test templatetag ``vola_plugin``:

        Returns a single plugin

        Usage:
        {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" as var %}
        {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" language="de" as var %}

        Optional keyword arguments:
        template_prefix, template_suffix, language
        """
        self.client.login(username="superuser", password="superuser")
        request = self.factory.get(reverse("admin:vola_container_changelist"))

        # testing with a plugin being rendered
        # u'<div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div>'
        PluginLatestBlogEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, slug="blogentries", position=0, limit=2)
        PluginLatestCustomEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, slug="customentries", position=1, limit=2)
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_plugin "home" "main" "blogentries" as plugin %}
        {{ plugin }}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""Latest Blog Entries""")
        # we just get the plugin, so we can render it now
        # this is similar to vola_rendered_plugin below
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_plugin "home" "main" "blogentries" as plugin %}
        {% vola_render plugin as content %}{{ content }}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div>""")
        # we can also get the plugins data
        # this is similar to vola_data_plugin below
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_plugin "home" "main" "blogentries" as plugin %}
        {% vola_data plugin as content %}{% for object in content %}<div class="obj">{{ object.title }}</div>{% endfor %}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div>""")

        # check caching
        cache_key = get_cache_key("volaplugin", "home", "main", "blogentries")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, PluginLatestBlogEntries.objects.get(container=self.container_page_home))
        # now add a plugin (this invalidates the cache_group)
        PluginSnippet.objects.create(container=self.container_page_home, group=self.group_page_home_main, position=2, title=u"snippet", body=u"xxx")
        # cache should now be empty
        # FIXME: the single plugin cache does not necessarily need to be
        # invalidated with the group
        cache_key = get_cache_key("volaplugin", "home", "main", "blogentries")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, None)
        # using templatetag generates the new cache
        t = template.Template("""{% load vola_tags %}{% vola_plugin "home" "main" "blogentries" as plugin %}""")
        t.render(template.RequestContext(request, {}))
        # cache should be updated
        cache_key = get_cache_key("volaplugin", "home", "main", "blogentries")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, PluginLatestBlogEntries.objects.get(container=self.container_page_home))

        # FIXME: how do we test caching with updating subitems since
        # this tag only caches the plugin (but not its contents).

    def test_vola_rendered_plugin(self):
        """
        Test templatetag ``vola_rendered_plugin``:

        Returns a single rendered plugin

        Usage:
        {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" as var %}
        {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" language="de" as var %}

        Optional keyword arguments:
        template_prefix, template_suffix, language
        """
        self.client.login(username="superuser", password="superuser")
        request = self.factory.get(reverse("admin:vola_container_changelist"))

        # testing with a plugin being rendered
        # u'<div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div>'
        PluginLatestBlogEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, slug="blogentries", position=0, limit=2)
        PluginLatestCustomEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, slug="customentries", position=1, limit=2)
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_rendered_plugin "home" "main" "blogentries" as content %}
        {{ content }}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div>""")

        # check caching
        cache_key = get_cache_key("volarenderedplugin", "home", "main", "blogentries")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, '<div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div>')
        # now add a plugin (this invalidates the cache_group)
        PluginSnippet.objects.create(container=self.container_page_home, group=self.group_page_home_main, position=2, title=u"snippet", body=u"xxx")
        # cache should now be empty
        # FIXME: the single plugin cache does not necessarily need to be
        # invalidated with the group
        cache_key = get_cache_key("volarenderedplugin", "home", "main", "blogentries")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, None)
        # using templatetag generates the new cache
        t = template.Template("""{% load vola_tags %}{% vola_rendered_plugin "home" "main" "blogentries" as content %}""")
        t.render(template.RequestContext(request, {}))
        # cache should be updated
        cache_key = get_cache_key("volarenderedplugin", "home", "main", "blogentries")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, '<div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div>')

        # check caching with changing subitems
        # adding blog entry so it shows up first
        BlogEntry.objects.create(id=1000, title=u"Blog Entry Nr. 1000", pub_date=datetime.date.today()+datetime.timedelta(days=1))
        # we should now get the updated blog entry
        # because of our custom cache callback
        t = template.Template("""{% load vola_tags %}{% vola_rendered_plugin "home" "main" "blogentries" as content %}""")
        t.render(template.RequestContext(request, {}))
        # cache should be updated
        cache_key = get_cache_key("volarenderedplugin", "home", "main", "blogentries")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, '<div class="obj">Blog Entry Nr. 1000</div><div class="obj">Blog Entry Nr. 1</div>')

    def test_vola_data_plugin(self):
        """
        Test templatetag ``vola_data_plugin``:

        Returns a single rendered plugin

        Usage:
        {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" as var %}
        {% vola_rendered_plugin "container_slug" "group_slug" "plugin_slug" language="de" as var %}

        Optional keyword arguments:
        template_prefix, template_suffix, language
        """
        self.client.login(username="superuser", password="superuser")
        request = self.factory.get(reverse("admin:vola_container_changelist"))

        # testing with a plugin being rendered
        # [<BlogEntry: Blog Entry Nr. 1>, <BlogEntry: Blog Entry Nr. 2>]
        PluginLatestBlogEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, slug="blogentries", position=0, limit=2)
        PluginLatestCustomEntries.objects.create(container=self.container_page_home, group=self.group_page_home_main, slug="customentries", position=1, limit=2)
        t = template.Template("""{% spaceless %}{% load vola_tags %}
        {% vola_data_plugin "home" "main" "blogentries" as content %}
        {% for object in content %}<div class="obj">{{ object.title }}</div>{% endfor %}{% endspaceless %}""")
        c = template.RequestContext(request, {})
        self.assertEqual(t.render(c), u"""<div class="obj">Blog Entry Nr. 1</div><div class="obj">Blog Entry Nr. 2</div>""")

        # check caching
        cache_key = get_cache_key("voladataplugin", "home", "main", "blogentries")
        result_list = cache.get(cache_key, None)
        self.assertQuerysetEqual(result_list, ["<BlogEntry: Blog Entry Nr. 1>", "<BlogEntry: Blog Entry Nr. 2>"])
        # now add a plugin (this invalidates the cache_group)
        PluginSnippet.objects.create(container=self.container_page_home, group=self.group_page_home_main, position=2, title=u"snippet", body=u"xxx")
        # cache should now be empty
        # FIXME: the single plugin cache does not necessarily need to be
        # invalidated with the group
        cache_key = get_cache_key("voladataplugin", "home", "main", "blogentries")
        result_list = cache.get(cache_key, None)
        self.assertEqual(result_list, None)
        # using templatetag generates the new cache
        t = template.Template("""{% load vola_tags %}{% vola_data_plugin "home" "main" "blogentries" as content %}""")
        t.render(template.RequestContext(request, {}))
        # cache should be updated
        cache_key = get_cache_key("voladataplugin", "home", "main", "blogentries")
        result_list = cache.get(cache_key, None)
        self.assertQuerysetEqual(result_list, ["<BlogEntry: Blog Entry Nr. 1>", "<BlogEntry: Blog Entry Nr. 2>"])

        # check caching with changing subitems
        # adding blog entry so it shows up first
        BlogEntry.objects.create(id=1000, title=u"Blog Entry Nr. 1000", pub_date=datetime.date.today()+datetime.timedelta(days=1))
        # we should now get the updated blog entry
        # because of our custom cache callback
        t = template.Template("""{% load vola_tags %}{% vola_data_plugin "home" "main" "blogentries" as content %}""")
        t.render(template.RequestContext(request, {}))
        # cache should be updated
        cache_key = get_cache_key("voladataplugin", "home", "main", "blogentries")
        result_list = cache.get(cache_key, None)
        self.assertQuerysetEqual(result_list, ["<BlogEntry: Blog Entry Nr. 1000>", "<BlogEntry: Blog Entry Nr. 1>"])

