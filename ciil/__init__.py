import os

# Avoid native MySQL client build; use pure-Python driver when MySQL is enabled.
if os.getenv("DB_ENGINE", "sqlite").lower() == "mysql":
	try:
		import pymysql

		pymysql.install_as_MySQLdb()
	except ImportError:
		# If the package is missing, Django will still error clearly on startup.
		pass
