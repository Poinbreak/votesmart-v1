"""
WSGI config for VoteSmart TN project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'votesmart.settings')
application = get_wsgi_application()
