# coding: utf-8

# PYTHON IMPORTS
import datetime

# DJANGO IMPORTS
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission

# PROJECT IMPORTS
from vola.models import Category, Container, Group, Plugin

# CONSTANTS
password = 'mypassword'


class VolalTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        
        # users
        self.user_superuser = User.objects.create_superuser("superuser", "superuser@volaproject.com", password)
        self.user_editor = User.objects.create_user("editor", "editor@volaproject.com", password)
        self.user_editor.is_staff = True
        self.user_editor.save()
        self.user_website = User.objects.create_user("user", "user@volaproject.com", password)
        # categories
        self.category_pages = Category.objects.create(id=1, name="Pages", position=0)
        self.category_snippets = Category.objects.create(id=2, name="Snippets", position=1)
        # containers
        self.container_page_home = Container.objects.create(id=1, name="Home", slug="home", category=self.category_pages)
        self.container_page_blog = Container.objects.create(id=2, name="Blog", slug="blog", category=self.category_pages)
        self.container_snippets = Container.objects.create(id=3, name="Snippets", slug="snippets", category=self.category_snippets)
        # groups (only for home)
        self.group_page_home_main = Group.objects.create(id=1, container=self.container_page_home, name="Main", slug="main", flag_menu=True, position=0)
        self.group_page_home_sidebar = Group.objects.create(id=2, container=self.container_page_home, name="Sidebar", slug="sidebar", flag_menu=True, position=1)


class VolaBasicTests(VolalTestCase):
    
    def test_objects_created(self):
        """
        Test that objects have been created.
        """
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Category.objects.count(), 2)
        self.assertEqual(Container.objects.count(), 3)
        self.assertEqual(Group.objects.count(), 2)
        self.assertEqual(Plugin.objects.count(), 0)

    def test_urls(self):
        """
        Check URLs, no login
        """
        # login required
        # resonse 200, because we are redirected to the login page
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
        response = self.client.get(reverse("admin:vola_container_make_preview", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[1]))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:vola_container_group", args=[1,1]))
        self.assertEqual(response.status_code, 200)

    def test_login_superuser(self):
        """
        Test login, superuser
        """
        # login with superuser
        self.client.login(username="superuser", password=password)
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
        # make preview redirects to the new preview container
        response = self.client.get(reverse("admin:vola_container_make_preview", args=[1]))
        self.assertRedirects(response, reverse("admin:vola_container_change", args=[4]), status_code=302, target_status_code=200)
        self.assertEqual(Container.objects.count(), 4)
        self.assertEqual(Group.objects.count(), 4)
        # transfer preview redirects to the new preview container
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[4]))
        self.assertRedirects(response, reverse("admin:vola_container_change", args=[1]), status_code=302, target_status_code=200)
        self.assertEqual(Container.objects.count(), 3)
        self.assertEqual(Group.objects.count(), 2)
        # now we have groups with IDs 5 and 6 (make_preview generates 3 and 4)
        response = self.client.get(reverse("admin:vola_container_group", args=[1,5]))
        self.assertEqual(response.status_code, 200)
        # logout
        self.client.logout()

    def test_login_editor(self):
        """
        Test login, editor without permissions
        """
        # login with editor
        # no permissions are given, so response is always 403
        self.client.login(username="editor", password=password)
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_add"))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_delete", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_history", args=[1]))
        self.assertEqual(response.status_code, 200) # no permissions needed if user.is_staff
        response = self.client.get(reverse("admin:vola_container_make_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[1]))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse("admin:vola_container_group", args=[1,1]))
        self.assertEqual(response.status_code, 403)
        # logout
        self.client.logout()

    # def test_login_editor_permissions(self):
    #     """
    #     Test login, editor with permissions
    #     """
    #     print "XXX:", self.user_editor.get_all_permissions()
    #     # login with editor
    #     # no permissions are given, so response is always 403
    #     self.client.login(username="editor", password=password)
    #     response = self.client.get(reverse("admin:vola_container_changelist"))
    #     self.assertEqual(response.status_code, 403)
    #     response = self.client.get(reverse("admin:vola_container_add"))
    #     self.assertEqual(response.status_code, 403)
    #     response = self.client.get(reverse("admin:vola_container_change", args=[1]))
    #     self.assertEqual(response.status_code, 403)
    #     response = self.client.get(reverse("admin:vola_container_delete", args=[1]))
    #     self.assertEqual(response.status_code, 403)
    #     response = self.client.get(reverse("admin:vola_container_history", args=[1]))
    #     self.assertEqual(response.status_code, 200) # no permissions needed if user.is_staff
    #     response = self.client.get(reverse("admin:vola_container_make_preview", args=[1]))
    #     self.assertEqual(response.status_code, 403)
    #     response = self.client.get(reverse("admin:vola_container_transfer_preview", args=[1]))
    #     self.assertEqual(response.status_code, 403)
    #     response = self.client.get(reverse("admin:vola_container_group", args=[1,1]))
    #     self.assertEqual(response.status_code, 403)
    #     # logout
    #     self.client.logout()


class VolaModelTests(VolalTestCase):
    
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
        self.assertEqual(Group.objects.count(), 2)
        # required: name, slug
        g = Group.objects.create(container=self.container_page_home, name="Test", slug="test", position=2)
        self.assertEqual(Group.objects.count(), 3)
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
        self.client.login(username="superuser", password=password)
        response = self.client.get(reverse("admin:vola_container_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_container_add(self):
        """
        Test add container
        """
        pass

    def test_container_edit(self):
        """
        Test edit container
        
        We only need to test extra_context, since everything else is
        a standard change_form with inlines
        """
        self.client.login(username="superuser", password=password)
        response = self.client.get(reverse("admin:vola_container_change", args=[1]))
        self.assertEqual(response.status_code, 200)
        # 2 groups, no additional groups
        self.assertEqual(len(response.context["groups"]), 2)
        self.assertEqual(len(response.context["groups_additional"]), 0)
        # add additional group
        g = Group.objects.create(container=self.container_page_home, name="Test", slug="test", flag_menu=False, position=2)
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

    def test_container_make_preview(self):
        """
        Test make preview
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

    
