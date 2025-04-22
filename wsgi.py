import eventlet
eventlet.monkey_patch()  # Make sure this is at the very top

from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return "Hello, World!"

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)

