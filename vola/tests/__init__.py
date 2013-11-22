# coding: utf-8

# PYTHON IMPORTS
import datetime

# DJANGO IMPORTS
from django.test import TestCase
from django.test.client import Client, RequestFactory
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission as DjangoPermission
from django.contrib.contenttypes.models import ContentType

# PROJECT IMPORTS
from vola.models import Language, Category, Container, Group, Plugin, Permission


class VolalTestCase(TestCase):
    
    def setUp(self):
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

    
