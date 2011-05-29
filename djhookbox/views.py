# Part of django-hookbox
# Copyright 2011, Duane Griffin <duaneg@dghda.com>

from django.conf import settings
from django.dispatch import Signal
from django.http import HttpResponse
from django.template import loader, RequestContext
from django.views.decorators.csrf import csrf_exempt

import json
import logging

logger = logging.getLogger('djhookbox')
secret = getattr(settings, 'HOOKBOX_WEBHOOK_SECRET', None)

_callbacks = []

def _call_callbacks(op, *args, **kwargs):
    result = None
    for callback in [cb for (cbop, cb) in _callbacks if cbop is None or cbop == op]:
        oneresult = callback(op, *args, **kwargs)
        if result is None:
            result = oneresult
        elif not oneresult is None:
            logger.warn("multiple results returned from %s callback" % op)
    return result

def whcallback(arg):
    '''
    Decorator for functions which handle webhook callbacks.

    Functions must take three arguments: the operation type, user and
    *optional* channel name. The latter will only be provided for
    operations on a channel (i.e. not connect/disconnect).

    If a string argument is given the function will only be called for
    matching webhooks. If no argument is given it will be called for all
    webhooks.

    Webhooks may optionally return a result, handling of which is dependent on
    the operation type:
     - The connect/disconnect operations ignore any results.
     - Create callbacks should return either a dict containing the channel
       options or, if they want to disallow channel creation, a failure
       message (string).
       If no create callback returns a response the operation is deemed to have
       *failed*.
     - Other callbacks may return a failure message (string), a
       dictionary (which will be returned as a successful response), or a
       properly formatted hookbox response.
       If no callback returns a response the operation will be deemed to have
       *succeded* and an empty success response will be returned.

    In all cases, including connect/disconnect, if more that one callback
    returns a result the first will be used and a warning will be logged.
    '''

    # Called without op arg: register the callback for all operations
    if callable(arg):
        _callbacks.append((None, arg))
        return arg

    # Otherwise only register the callback for the specified operation
    def decorator(method):
        _callbacks.append((arg, method))
    return decorator

# TODO: Not sure these are necessary any more, the callbacks provide a super-set
#       of their functionality.
signals = {
    'connect':     Signal(),
    'disconnect':  Signal(),
    'subscribe':   Signal(providing_args = ['channel']),
    'unsubscribe': Signal(providing_args = ['channel']),
}

def webhook(method):
    '''
    Decorator which:
     - checks a WebHook's secret key is correct
     - exempts the view from CSRF checks
     - massages the return result into the format expected by hookbox

    Returns 403 if the secret is required and not present/incorrect.
    '''

    @csrf_exempt
    def wrapper(*args, **kwargs):
        request = args[0]
        if secret is None or ('secret' in request.POST and request.POST['secret'] == secret):
            try:
                data = method(*args, **kwargs)
                if data is None:
                    result = [True, {}]
                elif isinstance(data, dict):
                    result = [True, data]
                elif isinstance(data, str):
                    result = [False, {'msg': data}]
                else:
                    assert isinstance(data, list)
                    assert len(data) == 2
                    result = data
            except Exception as err:
                result = [False, {'msg': str(err)}]
        else:
            result = [False, {'msg': 'webhook secret verification failed'}]
        return HttpResponse(json.dumps(result), mimetype = 'application/json')

    return wrapper

@webhook
def connect(request):
    signals['connect'].send(request.user)
    _call_callbacks('connect', request.user)
    return {
        'name': request.user.username
    }

@webhook
def disconnect(request):
    signals['disconnect'].send_robust(request.user)
    _call_callbacks('disconnect', request.user)

@webhook
def create_channel(request):
    result = _call_callbacks('create', request.user, request.POST['channel_name'])
    return result or [False, {'msg': 'unrecognized channel: %s' % request.POST['channel_name']}]

@webhook
def destroy_channel(request):
    return _call_callbacks('destroy', request.user, channel = request.POST['channel_name'])

@webhook
def subscribe(request):
    signals['subscribe'].send(request.user, channel = request.POST['channel_name'])
    return _call_callbacks('subscribe', request.user, channel = request.POST['channel_name'])

@webhook
def unsubscribe(request):
    signals['unsubscribe'].send_robust(request.user, channel = request.POST['channel_name'])
    return _call_callbacks('unsubscribe', request.user, channel = request.POST['channel_name'])
