# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Language'
        db.create_table('vola_language', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=7)),
            ('position', self.gf('django.db.models.fields.IntegerField')(default=-1)),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('vola', ['Language'])

        # Adding model 'Category'
        db.create_table('vola_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('position', self.gf('django.db.models.fields.IntegerField')(default=-1)),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('vola', ['Category'])

        # Adding model 'Container'
        db.create_table('vola_container', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=200)),
            ('cache_key', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=200)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='containers', null=True, to=orm['vola.Category'])),
            ('preview', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('preview_url', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('transfer_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('transfer_container', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='previews', null=True, to=orm['vola.Container'])),
            ('site', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sites.Site'], null=True, blank=True)),
            ('position', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('vola', ['Container'])

        # Adding model 'Group'
        db.create_table('vola_group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('container', self.gf('django.db.models.fields.related.ForeignKey')(related_name='groups', to=orm['vola.Container'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=200)),
            ('cache_key', self.gf('django.db.models.fields.SlugField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('plugins_include', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('plugins_exclude', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('menu', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('position', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('vola', ['Group'])

        # Adding unique constraint on 'Group', fields ['container', 'slug']
        db.create_unique('vola_group', ['container_id', 'slug'])

        # Adding unique constraint on 'Group', fields ['container', 'cache_key']
        db.create_unique('vola_group', ['container_id', 'cache_key'])

        # Adding model 'Plugin'
        db.create_table('vola_plugin', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('container', self.gf('django.db.models.fields.related.ForeignKey')(related_name='plugins', to=orm['vola.Container'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='plugins', null=True, to=orm['vola.Group'])),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='plugins', null=True, to=orm['vola.Language'])),
            ('app_label', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('model_name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('lock_content', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('lock_position', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('position', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('vola', ['Plugin'])

        # Adding model 'Permission'
        db.create_table('vola_permission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('container', self.gf('django.db.models.fields.related.ForeignKey')(related_name='permissions', to=orm['vola.Container'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='vola_permissions', null=True, to=orm['auth.User'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='vola_permissions', null=True, to=orm['auth.Group'])),
            ('manage_container', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('manage_preview', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('manage_plugins', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('create_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('update_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('vola', ['Permission'])

        # Adding unique constraint on 'Permission', fields ['container', 'user', 'group']
        db.create_unique('vola_permission', ['container_id', 'user_id', 'group_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Permission', fields ['container', 'user', 'group']
        db.delete_unique('vola_permission', ['container_id', 'user_id', 'group_id'])

        # Removing unique constraint on 'Group', fields ['container', 'cache_key']
        db.delete_unique('vola_group', ['container_id', 'cache_key'])

        # Removing unique constraint on 'Group', fields ['container', 'slug']
        db.delete_unique('vola_group', ['container_id', 'slug'])

        # Deleting model 'Language'
        db.delete_table('vola_language')

        # Deleting model 'Category'
        db.delete_table('vola_category')

        # Deleting model 'Container'
        db.delete_table('vola_container')

        # Deleting model 'Group'
        db.delete_table('vola_group')

        # Deleting model 'Plugin'
        db.delete_table('vola_plugin')

        # Deleting model 'Permission'
        db.delete_table('vola_permission')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'vola.category': {
            'Meta': {'ordering': "['position']", 'object_name': 'Category'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'vola.container': {
            'Meta': {'ordering': "['name', '-preview']", 'object_name': 'Container'},
            'cache_key': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'containers'", 'null': 'True', 'to': "orm['vola.Category']"}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'position': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'preview': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'preview_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']", 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'transfer_container': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'previews'", 'null': 'True', 'to': "orm['vola.Container']"}),
            'transfer_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'vola.group': {
            'Meta': {'ordering': "['-menu', 'position']", 'unique_together': "(('container', 'slug'), ('container', 'cache_key'))", 'object_name': 'Group'},
            'cache_key': ('django.db.models.fields.SlugField', [], {'max_length': '200'}),
            'container': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'to': "orm['vola.Container']"}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'menu': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'plugins_exclude': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'plugins_include': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'position': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '200'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'vola.language': {
            'Meta': {'ordering': "['position']", 'object_name': 'Language'},
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '7'}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'vola.permission': {
            'Meta': {'unique_together': "(('container', 'user', 'group'),)", 'object_name': 'Permission'},
            'container': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'to': "orm['vola.Container']"}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vola_permissions'", 'null': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manage_container': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'manage_plugins': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'manage_preview': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vola_permissions'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'vola.plugin': {
            'Meta': {'ordering': "['position']", 'object_name': 'Plugin'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'container': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'plugins'", 'to': "orm['vola.Container']"}),
            'create_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'plugins'", 'null': 'True', 'to': "orm['vola.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'plugins'", 'null': 'True', 'to': "orm['vola.Language']"}),
            'lock_content': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lock_position': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'model_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'position': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'update_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['vola']