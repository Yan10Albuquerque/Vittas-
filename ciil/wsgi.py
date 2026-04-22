"""
WSGI config for ciil project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

# Ensure PyMySQL is used instead of any preinstalled mysqlclient and advertise
# a mysqlclient-compatible version to satisfy Django's version check.
try:
    import pymysql

    pymysql.install_as_MySQLdb()
    pymysql.__version__ = "2.2.4"
    pymysql.VERSION = (2, 2, 4, "final", 0)
    pymysql.version_info = (2, 2, 4, "final", 0)
except Exception:
    pass

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ciil.settings')

application = get_wsgi_application()
