from django.shortcuts import render

from djhookbox import whcallback

@whcallback('create')
def create_channel(op, user, channel):
    return {
        'history_size': 100,
        'reflective':   True,
        'presenceful':  True,
        'moderated':    False,
    }

def home(request):
    return render(request, 'base.html')
