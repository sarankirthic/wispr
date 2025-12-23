from app import app, socketio
import os

app = app


if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = os.getenv('FLASK_PORT', 5000)
    debug = os.getenv('FLASK_DEBUG', True)
    socketio.run(app, debug=debug, host=host, port=port)
