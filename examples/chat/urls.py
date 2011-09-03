from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'chat.views.home', name='home'),
    url(r'^hookbox/', include('djhookbox.urls')),

    url(r'^admin/', include(admin.site.urls)),
)
