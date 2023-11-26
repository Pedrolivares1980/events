import os

# SECRET_KEY used for securely signing the session cookie in Flask.
# It can be set as an environment variable. If not set, a default value is used.
SECRET_KEY = os.getenv('SECRET_KEY', 'not-set')

# SQLALCHEMY_DATABASE_URI specifies the connection string for the SQLAlchemy database.
# It can be set as an environment variable. If not set, a default SQLite database is used.
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
