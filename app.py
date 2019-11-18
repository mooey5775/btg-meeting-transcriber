from flask import Flask, render_template, request, copy_current_request_context
from flask_socketio import SocketIO, emit, send, ConnectionRefusedError
import logging
import base64
import configparser
import time
import threading
import json

import websocket
from websocket._abnf import ABNF

REGION_MAP = {
    'us-east': 'gateway-wdc.watsonplatform.net',
    'us-south': 'stream.watsonplatform.net',
    'eu-gb': 'stream.watsonplatform.net',
    'eu-de': 'stream-fra.watsonplatform.net',
    'au-syd': 'gateway-syd.watsonplatform.net',
    'jp-tok': 'gateway-syd.watsonplatform.net',
}
app = Flask(__name__, static_url_path='', static_folder='static')
logging.basicConfig(level=logging.DEBUG)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

sockets = {}
sock_open = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('audio-start', namespace='/audio-sock')
def start_audio_tx():
    app.logger.info(f"Starting audio stream from {request.sid}...")
    sock_open[request.sid] = False
    @copy_current_request_context
    def _on_open(ws):
        on_open(request.sid)(ws)
        app.logger.info(f"Started audio stream from {request.sid}")
    ws = websocket.WebSocketApp(url,
                                header=headers,
                                on_message=on_message(request.sid),
                                on_error=on_error(request.sid),
                                on_close=on_close(request.sid))
    ws.on_open = _on_open
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    socketio.emit("audio-started", namespace="/audio-sock")

    sockets[request.sid] = ws

@socketio.on('audio-tx', namespace='/audio-sock')
def recv_audio_tx(audio):
    app.logger.info(f"Sending length {len(audio)}")
    if request.sid not in sockets:
        raise ConnectionRefusedError('No audio connection open!')
    app.logger.info(f"Received audio chunk from {request.sid}")
    sockets[request.sid].send(audio, ABNF.OPCODE_BINARY)

@socketio.on('audio-stop', namespace='/audio-sock')
def stop_audio_tx():
    if request.sid not in sockets or sock_open[request.sid] == False:
        raise ConnectionRefusedError('No audio connection open!')
    app.logger.info(f"Stopping audio stream from {request.sid}")
    data = {"action": "stop"}
    sockets[request.sid].send(json.dumps(data).encode('utf8'))
    # ... which we need to wait for before we shutdown the websocket
    time.sleep(1)
    sockets[request.sid].close()
    del sockets[request.sid]
    emit("trnsc-result", "testing...")

def get_auth():
    config = configparser.RawConfigParser()
    config.read('speech.cfg')
    apikey = config.get('auth', 'apikey')
    return ("apikey", apikey)

def get_url():
    config = configparser.RawConfigParser()
    config.read('speech.cfg')
    region = config.get('auth', 'region')
    host = REGION_MAP[region]
    return ("wss://{}/speech-to-text/api/v1/recognize"
           "?model=en-US_BroadbandModel").format(host)

def on_message(sid):
    def _on(ws, msg):
        app.logger.info(msg)
    return _on

def on_error(sid):
    def _on(ws, msg):
        app.logger.error(msg)
        del sockets[sid]
    return _on

def on_close(sid):
    def _on(ws):
        pass
    return _on

def on_open(sid):
    def _on(ws):
        """Triggered as soon a we have an active connection."""
        data = {
            "action": "start",
            # this means we get to send it straight raw sampling
            "content-type": "audio/wav",
            "continuous": True,
            "interim_results": True,
            "inactivity_timeout": 30, # in order to use this effectively
            # you need other tests to handle what happens if the socket is
            # closed by the server.
            "word_confidence": True,
            "speaker_labels": True,
            "timestamps": True,
            "max_alternatives": 3
        }

        # Send the initial control message which sets expectations for the
        # binary stream that follows:
        ws.send(json.dumps(data).encode('utf8'))
        time.sleep(1)
        sock_open[sid] = True
    return _on

if __name__ == '__main__':
    headers = {}
    userpass = ":".join(get_auth())
    headers["Authorization"] = "Basic " + base64.b64encode(userpass.encode()).decode()
    url = get_url()

    #websocket.enableTrace(True)

    socketio.run(app, debug=True)
