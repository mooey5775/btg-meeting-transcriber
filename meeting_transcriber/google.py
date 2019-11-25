from google.cloud import speech_v1p1beta1 as speech
import time
import logging
from collections import Counter

def get_current_time():
    return int(round(time.time() * 1000))

def get_main_speaker(result):
    cnt = Counter()
    for word in result.alternatives[0].words:
        cnt[word.speaker_tag] += 1
    return cnt.most_common(1)[0][0]

def manage_stream(mic, finals, STREAMING_LIMIT):
    client = speech.SpeechClient()
    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code='en-US',
        max_alternatives=1,
        enable_speaker_diarization=True,
        enable_automatic_punctuation=True)
    streaming_config = speech.types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

    with mic as stream:
        while not stream.to_close:
            audio_generator = stream.generator()

            requests = (speech.types.StreamingRecognizeRequest(
                        audio_content=content) for content in audio_generator)

            responses = client.streaming_recognize(streaming_config, requests)

            logging.info("Started new stream")

            for response in responses:
                logging.info("new response")

                if stream.to_close:
                    break

                if get_current_time() - stream.start_time > STREAMING_LIMIT:
                    stream.start_time = get_current_time()
                    break

                if not response.results:
                    continue

                result = response.results[0]

                if not result.alternatives:
                    continue

                if result.is_final:
                    transcript = result.alternatives[0].transcript
                    logging.info(transcript)

                    result_seconds = 0
                    result_nanos = 0

                    if result.result_end_time.seconds:
                        result_seconds = result.result_end_time.seconds

                    if result.result_end_time.nanos:
                        result_nanos = result.result_end_time.nanos

                    stream.end_time = int((result_seconds * 1000)
                                         + (result_nanos / 1000000))

                    finals.append(f"Speaker {get_main_speaker(result)}: {transcript}<br/><br/>")
                    stream.last_interim = ""
                else:
                    stream.last_interim = result.alternatives[0].transcript

            stream.next_stream()
