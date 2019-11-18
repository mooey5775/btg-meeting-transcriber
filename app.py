from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, send, ConnectionRefusedError
import logging

app = Flask(__name__, static_url_path='', static_folder='static')
logging.basicConfig(level=logging.DEBUG)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

sockets = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('audio-start', namespace='/audio-sock')
def start_audio_tx():
    app.logger.info(f"Started audio stream from {request.sid}")
    sockets[request.sid] = "1"

@socketio.on('audio-tx', namespace='/audio-sock')
def recv_audio_tx(audio):
    if request.sid not in sockets:
        raise ConnectionRefusedError('No audio connection open!')
    app.logger.info(f"Received audio chunk from {request.sid}")
    with open('test.wav', 'wb') as f:
        f.write(audio)

@socketio.on('audio-stop', namespace='/audio-sock')
def stop_audio_tx():
    if request.sid not in sockets:
        raise ConnectionRefusedError('No audio connection open!')
    app.logger.info(f"Stopping audio stream from {request.sid}")
    del sockets[request.sid]
    emit("trnsc-result", "testing...")

if __name__ == '__main__':
    socketio.run(app, debug=True)
