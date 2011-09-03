# Django settings for example chat project.

import os
import sys

import hookbox

# Add the containing django-hookbox module to start of path
sys.path.insert(0, os.path.join(sys.path[0], '..', '..'))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Return an absolute path relative to this file's directory
def base(*paths):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), *paths))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':   base('var', 'chat.db'),
    }
}

USE_I18N = False
USE_L10N = True
TIME_ZONE = None
LANGUAGE_CODE = 'en-uk'

SITE_ID = 1

MEDIA_ROOT = base('var', 'media')
MEDIA_URL = '/media/'

STATIC_ROOT = base('var', 'static')
STATIC_URL = '/static/'

# Add the static files from the hookbox module
STATICFILES_DIRS = (
    os.path.abspath(os.path.join(os.path.dirname(__file__), 'static')),
    os.path.abspath(os.path.join(os.path.dirname(hookbox.__file__), 'static')),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

ADMIN_MEDIA_PREFIX = '/static/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'n@%%9i)7fe+sk#d6g-n=4*o+5t1l7i9^ilie27t88jl-gbhqa='

HOOKBOX_WEBHOOK_SECRET = 'SECRET1'
HOOKBOX_API_SECURITY_TOKEN = 'SECRET2'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'chat.urls'

TEMPLATE_DIRS = (
    base('templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'djhookbox',
    'django.contrib.admin',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
