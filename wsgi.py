import eventlet
eventlet.monkey_patch()

from app import app
from flask_socketio import SocketIO

# Initialize SocketIO
socketio = SocketIO(app)

# This part is not needed for deployment with Gunicorn
# Gunicorn will automatically look for the app in `wsgi.py`
