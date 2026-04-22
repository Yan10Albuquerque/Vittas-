#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Force PyMySQL to act as MySQLdb before Django imports the DB backend.
# Django 6 checks for mysqlclient>=2.2.1; we bump the exposed version info so
# the pure-Python driver passes the check on Railpack images that ship an old
# mysqlclient.
try:
    import pymysql

    pymysql.install_as_MySQLdb()
    pymysql.__version__ = "2.2.4"
    pymysql.VERSION = (2, 2, 4, "final", 0)
    pymysql.version_info = (2, 2, 4, "final", 0)
except Exception:
    # If PyMySQL is not installed, Django will error explicitly later.
    pass


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ciil.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
