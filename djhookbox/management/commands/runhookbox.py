# Part of django-hookbox
# Copyright 2011, Duane Griffin <duaneg@dghda.com>

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.core.management.commands import runserver

import atexit
import os
import subprocess
import sys

from optparse import make_option

class Command(NoArgsCommand):

    # TODO: Would be nice to use OptionGroups here
    option_list = NoArgsCommand.option_list + (
        make_option('-e', '--executable',
                    default = os.path.join(os.path.dirname(sys.executable), 'hookbox'),
                    help = 'hookbox executable', metavar = 'EXE'),

        make_option('-i', '--interface', help = 'the interface hookbox binds to'),
        make_option('-p', '--port',      help = 'the port hookbox binds to'),

        make_option('--cbhost', help = 'the callback host', metavar = 'HOST'),
        make_option('--cbport', help = 'the callback path prefix', metavar = 'PORT'),
        make_option('--cbpath', help = 'the callback path prefix [/hookbox]'),

        make_option('-s', '--webhook-secret',     help = 'callback secret token (passed to django by hookbox)', metavar = 'SECRET'),
        make_option('-r', '--api-security-token', help = 'web API secret token (passed to hookbox by django)', metavar = 'SECRET'),
        make_option('-a', '--admin-password',     help = 'hookbox administrator password', metavar = 'PASSWD'),
    )

    help = 'Start a hookbox server.'

    def start_hookbox(self, options, **kwargs):
        def addopt(args, opt):
            """Adds a hookbox command-line argument.

            If an argument is specified on the runhookbox command-line, it is used.
            Otherwise if an argument is specified in settings, it is used."""

            value = None

            # Command-line options are stored in attributes with dashes replaced by underscores
            optvar = opt.replace('-', '_')

            # Configuration settings match cmd-line option names,
            # except uppercase and prefixed by HOOKBOX_
            setvar = 'HOOKBOX_%s' % optvar.upper()

            if not options.get(optvar) is None:
                value = options.get(optvar)
            elif hasattr(settings, setvar):
                value = getattr(settings, setvar)

            if value:
                hbargs.extend(['--%s' % opt, value])

        # TODO: Support runserver options for determining host/port
        hbargs = [options.get('executable'),
                  '--cbhost', 'localhost',
                  '--cbport', '8000']

        # Add hookbox command-line arguments as required
        addopt(hbargs, 'port')
        addopt(hbargs, 'interface')
        addopt(hbargs, 'cbhost')
        addopt(hbargs, 'cbport')
        addopt(hbargs, 'cbpath')
        addopt(hbargs, 'webhook-secret')
        addopt(hbargs, 'api-security-token')
        addopt(hbargs, 'admin-password')

        self.proc = subprocess.Popen(hbargs, **kwargs)

    def stop_hookbox(self):

        # Would be nice to be able to specify a timeout
        self.proc.terminate()
        self.proc.wait()

    def handle_noargs(self, **options):
        self.start_hookbox(options)
        atexit.register(self.stop_hookbox)
        try:
            self.proc.wait()
        except KeyboardInterrupt:
            pass
