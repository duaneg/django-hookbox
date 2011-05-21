# Part of django-hookbox
# Copyright 2011, Duane Griffin <duaneg@dghda.com>

from django.conf.urls.defaults import *

urlpatterns = patterns('djhookbox.views',
    url(r'^connect$',    'connect',    name = 'hookbox_connect'),
    url(r'^disconnect$', 'disconnect', name = 'hookbox_disconnect'),

    url(r'^create_channel$',  'create_channel',  name = 'hookbox_create_channel'),
    url(r'^destroy_channel$', 'destroy_channel', name = 'hookbox_destroy_channel'),

    url(r'^subscribe$',   'subscribe',   name = 'hookbox_subscribe'),
    url(r'^unsubscribe$', 'unsubscribe', name = 'hookbox_unsubscribe'),
)
