import os
from setuptools import find_packages, setup

ROOT = os.path.abspath(os.path.dirname(__file__))

setup(
    name = 'django-hookbox',
    version = '0.2',
    description = 'Integrate hookbox with Django.',
    long_description = open(os.path.join(ROOT, 'README.txt')).read(),
    author = 'Duane Griffin',
    author_email = 'duaneg@dghda.com',
    url = 'https://github.com/duaneg/django-hookbox',
    license = 'BSD',
    packages = find_packages(),
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Utilities',
    ],
)
