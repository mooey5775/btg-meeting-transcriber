from flask import Flask, render_template, request, copy_current_request_context
from flask_socketio import SocketIO, emit, send, ConnectionRefusedError
import logging
import base64
import configparser
import time
import threading
import json
import os

from meeting_transcriber import MicrophoneStream, manage_stream

app = Flask(__name__, static_url_path='', static_folder='static')
logging.basicConfig(level=logging.DEBUG)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

streams = {}
finals = {}

STREAMING_LIMIT = 50000

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('audio-start', namespace='/audio-sock')
def start_audio_tx():
    app.logger.info(f"Starting audio stream from {request.sid}...")
    streams[request.sid] = MicrophoneStream(STREAMING_LIMIT, request.sid)
    finals[request.sid] = []
    wst = threading.Thread(target=manage_stream, args=(streams[request.sid], finals[request.sid], STREAMING_LIMIT))
    wst.daemon = True
    wst.start()
    emit("audio-started")

@socketio.on('audio-tx', namespace='/audio-sock')
def recv_audio_tx(audio):
    if request.sid not in finals and streams[request.sid].to_close:
        raise ConnectionRefusedError('No audio connection open!')
    app.logger.info(f"Received audio chunk from {request.sid} of length {len(audio)}")
    streams[request.sid]._audio_rx(audio)
    transcript = "<br/>" + "".join(finals[request.sid]) + " " + streams[request.sid].last_interim
    emit("interim-result", transcript)

@socketio.on('audio-stop', namespace='/audio-sock')
def stop_audio_tx():
    if request.sid not in finals and streams[request.sid].to_close:
        raise ConnectionRefusedError('No audio connection open!')
    app.logger.info(f"Stopping audio stream from {request.sid}")
    streams[request.sid].to_close = True
    transcript = "".join(finals[request.sid])
    del finals[request.sid]
    del streams[request.sid]
    emit("trnsc-result", transcript)

if __name__ == '__main__':
    socketio.run(app, debug=True)
