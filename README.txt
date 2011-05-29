==============
IMPORTANT NOTE
==============

Although hookbox is a very quick and easy way to experiment with COMET, it is
not suitable for production use at this time. Unfortunately, at the time of
writing, the hookbox project looks moribund. Hopefully this situation changes
soon, but for the meantime this module should only be used for quick
prototypes and experimentation.

============
Requirements
============

    * Django 1.3+
    * Hookbox 0.3.3
    * testfixtures 1.9.2+ (for unit tests)

It should work with Django 1.2 and earlier versions of testfixtures, however it
has not been tested. If you try it please let me know how you get on.

Other versions of hookbox (including the latest dev versions) probably will
*not* work, as things like command-line option names and URLs seem to change
frequently. On the other hand, any problems should be easy to fix.

============
Installation
============

Install the usual way, e.g.: ::

    pip install django-hookbox

Add to ``INSTALLED_APPS`` in ``settings.py``: ::

    INSTALLED_APPS = (
        ...
        'django_hookbox',
        ...
    )

Add to your ``urls.py``: ::

    urlpatterns = patterns('',
        ...
        (r'^hookbox/', include('djhookbox.urls')),
        ...

=============
CONFIGURATION
=============

At a minimum you will need a channel handler to allow channel creation. E.g.: ::

    @whcallback('create')
    def create_good_channels(op, user, channel = '-'):
        assert op == 'create'
        if channel.startswith('/good/'):
            return {
              'history_size': 1,
              'reflective':   False,
              'presenceful':  False,
              'moderated':    True,
            }
        elif channel.startswith('/bad/'):
            return 'no cookie for you!'

The first time a user subscribes to a channel it is implicitly created. If no
create callback returns an options dict this will fail.

To fail operations (e.g. deny a subscription attempt) provide callbacks that
return a failure message or raise an exception.

You will probably also want to configure various hookbox options in
``settings.py``. The available options are: ::

    HOOKBOX_INTERFACE: The interface the hookbox server listens on.
    HOOKBOX_PORT: The port the hookbox server listens on.
    HOOKBOX_CBHOST: The host the Django server listens on.
    HOOKBOX_CBPORT: The port the Django server listens on.
    HOOKBOX_CBPATH: The path prefix the webhook views are located under.
    HOOKBOX_WEBHOOK_SECRET: A secret token passed by hookbox to webhooks.
    HOOKBOX_REST_SECRET: A secret token passed by Django to hookbox.
    HOOKBOX_ADMIN_PASSWORD: The hookbox administrator password.

=====
USAGE
=====

A management command is provided to run the hookbox server. See
``./manage.py help runhookbox`` for the available options. By default options
from ``settings.py`` (see above) will be used.

To publish to a channel from with Django call, e.g.: ::

    djhookbox.publish('/some-channel/', {'data': 'some-data'})

