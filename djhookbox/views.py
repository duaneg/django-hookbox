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

channel_handlers = []

def register_channel_handler(handler):
    channel_handlers.append(handler)

def unregister_channel_handler(handler):
    channel_handlers.remove(handler)

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
     - exempts the view from CSRF checks.

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
                else:
                    assert isinstance(data, list)
                    assert len(list) == 2
            except Exception as err:
                result = [False, {'msg': str(err)}]
        else:
            result = [False, {'msg': 'webhook secret verification failed'}]
        return HttpResponse(json.dumps(result), mimetype = 'application/json')

    return wrapper

@webhook
def connect(request):
    signals['connect'].send(request.user)
    return {
        'name': request.user.username
    }

@webhook
def disconnect(request):
    signals['disconnect'].send_robust(request.user)

@webhook
def create_channel(request):

    # TODO: Allow handlers to veto create requests
    for handler in channel_handlers:
        opts = handler.create(request.user, request.POST['channel_name'])
        if not opts is None:
            return opts

    return [False, {}]

@webhook
def destroy_channel(request):
    pass

@webhook
def subscribe(request):
    signals['subscribe'].send(request.user, channel = request.POST['channel_name'])

@webhook
def unsubscribe(request):
    signals['unsubscribe'].send_robust(request.user, channel = request.POST['channel_name'])
