# coding: utf-8

# This is an example of a group validation function which you need to
# implement yourself and assign with each group via the admin interface.

# VOLA IMPORTS
from vola.models import Plugin


def group_validation(request, group, containeradminform, pluginadminforms):
    """
    Group validation

    Validate Plugins (resp. plugin forms) for a given Group. E.g., you are able to
    define custom validation where Plugin A depends on values of Plugin B or a
    specific User (or User Group).

    * request
        The current request (variables depending on your request context processors)
    * group
        The group object
    * pluginadminforms
        A list of AdminForms for already existing and new/extra Plugins for a given Group

    Please note that group_valid is called after validating each pluginform, so
    every instance is already being updated with the new values (though not saved yet).
    """
    print "USER:", request.user
    print "CONTAINER:", group.container
    print "GROUP:", group
    # pluginadminforms
    i = 0
    for adminform in pluginadminforms:
        # ORIGINAL PLUGIN
        try:
            print "ORIGINAL PLUGIN ID:", adminform.original.plugin_ptr_id
            p = Plugin.objects.get(id=adminform.original.plugin_ptr_id).get_plugin
            position_original = p.position
            position_updated = adminform.form.instance.position
            print "ORIGINAL PLUGIN (name, id, position):", p.__class__.__name__, p.id, p.position
            print "POSITION BEFORE (FROM ORIGINAL):", p.position
            print "POSITION AFTER (FROM INSTANCE):", adminform.form.instance.position
            # SET ERRORS
            if position_original != position_updated:
                adminform.form.errors["__all__"] = adminform.form.error_class([u"Moving plugin is not allowed."])
                #adminform.form.errors["slug"] = adminform.form.error_class([u"Slug error."])
        except:
            pass
        # COUNT ADMIN FORMS
        delete = adminform.form.data.get("%s-DELETE" % adminform.form.prefix, "0")
        if delete == "0": # raw data, therefore "0" instead of 0
            i = i + 1
    # SET GROUP ERRORS
    if i != 3:
        containeradminform.form.errors["__all__"] = containeradminform.form.error_class([u"Exactly 3 Plugins are needed."])
        

