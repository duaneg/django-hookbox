# Part of django-hookbox
# Copyright 2011, Duane Griffin <duaneg@dghda.com>

from django.conf import settings

from .views import whcallback

from BaseHTTPServer import BaseHTTPRequestHandler
import json # find faster lib
import urllib
import urllib2

class HookboxError(Exception):
    pass

def _server():
    interface = getattr(settings, 'HOOKBOX_INTERFACE', 'localhost')
    port = getattr(settings, 'HOOKBOX_PORT', '8001')
    return "http://%s:%s" % (interface, port)

apitoken = getattr(settings, 'HOOKBOX_API_SECURITY_TOKEN', None)

def _url(method):
    return '%s/web/%s' % (_server(), method)

def _send(method, data):
    if apitoken:
        data['security_token'] = apitoken

    try:
        req = urllib2.Request(_url(method), urllib.urlencode(data))
        resp = urllib2.urlopen(req)
        result = json.load(resp)
        if not result[0]:
            raise HookboxError(result[1]['msg'])
    except TypeError:
        raise HookboxError('could not decode response from hookbox')
    except urllib2.HTTPError as err:
        raise HookboxError("%s (%d)" % (BaseHTTPRequestHandler.responses[err.code][0], err.code))
    except urllib2.URLError as err:
        raise HookboxError(str(err.reason))

def create(channel):
    'Create a channel.'

    _send('create_channel', {
        'channel_name': channel,
    })

def publish(channel, payload):
    'Publish some data to a channel.'

    _send('publish', {
        'channel_name': channel,
        'payload':      json.dumps(payload),
    })

# TODO: set_state, et al methods
