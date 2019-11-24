from six.moves import queue
import time
import logging

class MicrophoneStream:
    def __init__(self, STREAMING_LIMIT, sid):
        self.data = queue.Queue()
        self.closed = False
        self.start_time = int(round(time.time() * 1000))
        self.audio_input = []
        self.last_audio_input = []
        self.end_time = 0
        self.offset = 0
        self.new_stream = True
        self.to_close = False
        self.sid = sid
        self.nonce = 0
        self.STREAMING_LIMIT = STREAMING_LIMIT
        self.last_interim = ""

    def __enter__(self):
        self.closed = False
        return self

    def __exit__(self, *args):
        self.closed = True
        self.data.put(None)

    def _audio_rx(self, audio):
        if self.closed:
            return
        logging.info("GOT AUDIO")
        self.data.put(audio)

    def next_stream(self):
        self.last_audio_input = self.audio_input
        self.audio_input = []
        self.new_stream = True
        self.last_interim = ""

    def generator(self):
        while not self.closed:
            res = []

            if self.new_stream and self.last_audio_input:

                chunk_time = self.STREAMING_LIMIT / len(self.last_audio_input)

                if chunk_time != 0:

                    if self.offset < 0:
                        self.offset = 0

                    if self.offset > self.end_time:
                        self.offset = self.end_time

                    chunks_from_ms = round((self.end_time -
                                            self.offset) / chunk_time)

                    self.offset = (round((
                        len(self.last_audio_input) - chunks_from_ms)
                                                  * chunk_time))

                    for i in range(chunks_from_ms, len(self.last_audio_input)):
                        res.append(self.last_audio_input[i])

                self.end_time = 0

                self.new_stream = False

            chunk = self.data.get()
            self.audio_input.append(chunk)

            if chunk is None:
                return
            res.append(chunk)

            while True:
                try:
                    chunk = self.data.get(block=False)

                    if chunk is None:
                        return
                    res.append(chunk)
                    self.audio_input.append(chunk)
                except queue.Empty:
                    break

            logging.info("SENDING...")
            yield b''.join(res)
