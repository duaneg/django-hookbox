# Part of django-hookbox
# Copyright 2011, Duane Griffin <duaneg@dghda.com>

from django.conf import settings
from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIHandler
from django.core.management.base import CommandError
from django.core.servers import basehttp
from django.core.urlresolvers import reverse
from django.dispatch import receiver
from django.test import TestCase

import djhookbox
from djhookbox.management.commands import runhookbox

import json
import logging
import os
import random
import re
import subprocess
import sys
import threading
import urllib

from testfixtures import LogCapture

# TODO: Set this from something sensible
verbose = False

connect_url = reverse('hookbox_connect')

# HACK: Next port to start the hookbox server on
#       Can't start & stop the server quickly on the same port as it doesn't
#       use SO_REUSEADDR
nextport = random.randint(10000, 20000)
HOOKBOX_STARTED = re.compile('hookbox - INFO - Listening to hookbox on http://([\w\d\.]+):(\d+)')

# Base code taken from: http://djangosnippets.org/snippets/1570/
class TestServerThread(threading.Thread):
    """
    Thread for running a http server while tests are running.

    Taken from: http://code.djangoproject.com/attachment/ticket/2879/django_live_server_r7936.diff
    with some modifications to avoid patching django.
    """

    def __init__(self, address, port):
        self.address = address
        self.port = port

        self._started = threading.Event()
        self._stopped = False
        self._error = None

        super(TestServerThread, self).__init__()

    def start(self):
        """ Start the server thread and wait for it to be ready """

        super(TestServerThread, self).start()
        self._started.wait()
        if self._error:
            raise self._error

    def stop(self):
        """ Stop the server """

        self._stopped = True

        # Send an http request to wake the server
        url = urllib.urlopen('http://%s:%d/en/fake/request/' % (self.address, self.port))
        url.read()

        # Wait for server to finish
        self.join(5)
        if self._error:
            raise self._error

    def run(self):
        """ Sets up test server and database and loops over handling http requests. """

        # Idea taken from: http://djangosnippets.org/snippets/2050/
        class QuietWSGIRequestHandler(basehttp.WSGIRequestHandler):
            def log_message(self, format, *args):
                if verbose:
                    return super(QuietWSGIRequestHandler, self).log_message(self, format, *args)

        try:
            handler = basehttp.AdminMediaHandler(WSGIHandler())
            server_address = (self.address, self.port)
            httpd = basehttp.WSGIServer(server_address, QuietWSGIRequestHandler)
            httpd.set_app(handler)
        except basehttp.WSGIServerException, e:
            self._error = e
        finally:
            self._started.set()

        # Loop until we get a stop event.
        while not self._stopped:
            httpd.handle_request()

def server(method):
    'Decorator that starts & stops hookbox for those tests that require it.'

    def wrapper(self, *args, **kwargs):
        global nextport

        # Start the test server
        server = TestServerThread('localhost', nextport)
        server.start()
        nextport += 1

        # Start hookbox
        hookboxcmd = runhookbox.Command()
        hookboxcmd.start_hookbox({
            'executable': os.path.join(os.path.dirname(sys.executable), 'hookbox'),
            'cbport': str(nextport - 1),
            'port': str(nextport),
            'admin-password': 'admin',
        }, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

        # TODO: Retry at different port if cannot bind
        #       This will be tricky, however, since hookbox prints the
        #       listening message *before* it binds...
        output = hookboxcmd.proc.stdout.readline()
        match = HOOKBOX_STARTED.search(output)
        if not match:
            hookboxcmd.proc.kill()
            raise CommandError('Could not start hookbox server')

        # Update hookbox settings to point to the running server
        settings.HOOKBOX_PORT = nextport
        nextport += 1

        # Perform the tests
        try:
            result = method(self, *args, **kwargs)
        finally:
            hookboxcmd.stop_hookbox()
            if verbose:
                for line in hookboxcmd.proc.stdout:
                    print line.strip('\n')
            server.stop()
        return result

    return wrapper

class DjangoHookboxTest(TestCase):

    def _cb_all(self, op, user, channel = '-'):
        if channel in self.all_calls:
            self.all_calls[channel] += 1
        else:
            self.all_calls[channel] = 1
        return None

    def _cb_create(self, op, user, channel = None):
        if channel in self.create_calls:
            self.create_calls[channel] += 1
        else:
            self.create_calls[channel] = 1

        if channel == '/a/':
            return {
                'history_size': 2,
                'reflective':   False,
                'presenceful':  False,
                'moderated':    True,
            }
        elif channel == '/b/':
            return 'denied'
        elif channel == '/c/':
            return [False, {'msg': 'also denied'}]
        else:
            return None

    def setUp(self):
        self.all_calls = {}
        self.create_calls = {}

        # HACK: don't allow other apps to mess with us or vice versa...
        self.old_cbs = djhookbox.views._callbacks
        djhookbox.views._callbacks = []
        djhookbox.whcallback(self._cb_all)
        djhookbox.whcallback('create')(self._cb_create)

        User.objects.create_user('a', 'a@example.com', 'a').save()

    def tearDown(self):
        djhookbox.views._callbacks = self.old_cbs

    @server
    def test_implicit_create(self):
        djhookbox.publish('/a/', json.dumps({'foo': 'bar'}))
        self.assertAllCalls({'/a/': 1})
        self.assertCreateCalls({'/a/': 1})

    @server
    def test_unauth_create(self):
        self.assertRaises(djhookbox.HookboxError,
                          djhookbox.publish, '/b/', json.dumps({'foo': 'bar'}))
        self.assertAllCalls({'/b/': 1})
        self.assertCreateCalls({'/b/': 1})

        self.assertRaises(djhookbox.HookboxError,
                          djhookbox.publish, '/c/', json.dumps({'foo': 'bar'}))
        self.assertAllCalls({'/b/': 1, '/c/': 1})
        self.assertCreateCalls({'/b/': 1, '/c/': 1})

    @server
    def test_rest_secret(self):
        secret = djhookbox.apitoken
        try:
            djhookbox.apitoken += '...not!'
            self.assertRaises(djhookbox.HookboxError,
                              djhookbox.publish, '/a/', json.dumps({'foo': 'bar'}))
            self.assertCreateCalls({})
        finally:
            djhookbox.apitoken = secret

    def test_webhook_secret(self):
        self.client.login(username = 'a', password = 'a')
        response = self.client.post(connect_url, {
            'channel_name': 'a',
            'secret':       djhookbox.views.secret,
        })
        self.assertSuccess(response)

        response = self.client.post(connect_url, {
            'channel_name': 'a',
        })
        data = self.decode(response)
        self.assertFalse(data[0], 'webhook secret verification should have failed')

        response = self.client.post(connect_url, {
            'channel_name': 'a',
            'secret':       djhookbox.views.secret + '...not!',
        })
        data = self.decode(response)
        self.assertFalse(data[0], 'webhook secret verification should have failed')

    def test_signals(self):
        class Listener(object):
            def __call__(self, *args, **kwargs):
                self.signal = kwargs.get('signal')
                self.sender = kwargs.get('sender').username
                self.kwargs = kwargs

        def doTest(which, params = dict(), **checks):
            listener = Listener()
            djhookbox.views.signals[which].connect(listener)

            self.client.login(username = 'a', password = 'a')
            params['secret'] = djhookbox.views.secret
            response = self.client.post(reverse('hookbox_%s' % which), params)

            self.assertSuccess(response)
            self.assertEquals(listener.sender, 'a')
            for (key, value) in checks.iteritems():
                self.assertEquals(listener.kwargs.get(key), value)

            self.client.logout()
            djhookbox.views.signals[which].disconnect(listener)

        doTest('connect')
        doTest('disconnect')
        doTest('subscribe', {'channel_name': 'b'}, channel = 'b')
        doTest('unsubscribe', {'channel_name': 'b'}, channel = 'b')

    def test_all_cbs(self):
        self.client.login(username = 'a', password = 'a')
        params = {
            'secret': djhookbox.views.secret,
            'channel_name': 'a',
        }

        response = self.client.post(reverse('hookbox_connect'), params)
        self.assertSuccess(response)
        self.assertAllCalls({'-': 1})

        response = self.client.post(reverse('hookbox_subscribe'), params)
        self.assertSuccess(response)
        self.assertAllCalls({'-': 1, 'a': 1})

        response = self.client.post(reverse('hookbox_destroy_channel'), params)
        self.assertSuccess(response)
        self.assertAllCalls({'-': 1, 'a': 2})

        response = self.client.post(reverse('hookbox_disconnect'), params)
        self.assertSuccess(response)
        self.assertAllCalls({'-': 2, 'a': 2})

    def test_warn_multiple_results(self):

        @djhookbox.whcallback
        def _cb_1(op, user, channel = '-'):
            return [True, {}]

        @djhookbox.whcallback
        def _cb_2(op, user, channel = '-'):
            return [True, {}]

        with LogCapture() as log:
            params = {'secret': djhookbox.views.secret}

            logging.getLogger('djhookbox').setLevel(logging.WARNING)

            response = self.client.post(reverse('hookbox_connect'), params)
            self.assertSuccess(response)
            self.assertAllCalls({'-': 1})

            response = self.client.post(reverse('hookbox_disconnect'), params)
            self.assertSuccess(response)
            self.assertAllCalls({'-': 2})

            log.check(
                ('djhookbox', 'WARNING', 'multiple results returned from connect callback'),
                ('djhookbox', 'WARNING', 'multiple results returned from disconnect callback'),
            )

    def test_explicit_deny(self):
        response = self.client.post(reverse('hookbox_create_channel'), {
            'secret': djhookbox.views.secret,
            'channel_name': '/b/',
        })

        data = self.decode(response)
        self.assertEquals(data[0], False, 'unexpected success')
        self.assertEquals(data[1], {'msg': 'denied'})
        self.assertAllCalls({'/b/': 1})

        response = self.client.post(reverse('hookbox_create_channel'), {
            'secret': djhookbox.views.secret,
            'channel_name': '/c/',
        })

        data = self.decode(response)
        self.assertEquals(data[0], False, 'unexpected success')
        self.assertEquals(data[1], {'msg': 'also denied'})
        self.assertAllCalls({'/b/': 1, '/c/': 1})

    def test_callback_error(self):

        @djhookbox.whcallback
        def _cb_1(op, user, channel = '-'):
            raise Exception('something bad')

        response = self.client.post(reverse('hookbox_create_channel'), {
            'secret': djhookbox.views.secret,
            'channel_name': '/a/',
        })

        data = self.decode(response)
        self.assertEquals(data[0], False, 'unexpected success')
        self.assertEquals(data[1], {'msg': 'something bad'})
        self.assertAllCalls({'/a/': 1})

    def decode(self, response):
        self.assertEquals(response.status_code, 200)
        self.assert_(('Content-Type', 'application/json') in response.items())

        result = json.loads(response.content)
        self.assert_(isinstance(result, list), 'unexpected result returned from server: %s' % str(result))
        self.assertEquals(len(result), 2)
        self.assert_(isinstance(result[0], bool), 'unexpected result returned from server: %s' % str(result))
        self.assert_(isinstance(result[1], dict), 'unexpected result returned from server: %s' % str(result))
        return result

    def assertSuccess(self, response):
        data = self.decode(response)
        if not data[0] and 'msg' in data[1]:
            self.fail(data[1]['msg'])
        else:
            self.assert_(data[0])

    def assertAllCalls(self, calls):
        self.assertEquals(self.all_calls, calls)

    def assertCreateCalls(self, calls):
        self.assertEquals(self.create_calls, calls)
