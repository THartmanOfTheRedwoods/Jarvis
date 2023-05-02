#!/usr/bin/env python

import zmq
import whisper
import numpy
import environment


class Brain:

    def __init__(self):
        self.id = "Jarvis"
        self.context = zmq.Context()
        # Receive work
        self.brain_relay = self.context.socket(zmq.PULL)
        self.brain_relay.connect("tcp://127.0.0.1:8000")
        # Send work
        self.consciousness_socket = self.context.socket(zmq.PUSH)
        self.consciousness_socket.connect("tcp://127.0.0.1:8001")  # was 5558

        # from pprint import pprint
        # pprint(whisper.available_models())
        # Loading whisper language models.
        # model = whisper.load_model("large-v2")
        print("Loading Jarvis language models.")
        self.language = "English"
        self.fp16 = False
        self.model = whisper.load_model("medium.en")  # Models in ~/.cache/whisper
        print("Brain is ready...")

    def process(self):
        while True:
            work = self.brain_relay.recv_json()
            audio_hex = work.get('ears', None)  # Should be sound bytes.
            if audio_hex:
                audio_bytes = bytes.fromhex(audio_hex)
                # Convert buffer to float32 using NumPy
                audio_as_np_int16 = numpy.frombuffer(audio_bytes, dtype=numpy.int16)
                audio_as_np_float32 = audio_as_np_int16.astype(numpy.float32)
                # Normalise float32 array so that values are between -1.0 and +1.0
                audio_normalised = audio_as_np_float32 * environment.SHORT_NORMALIZE
                print("Transcribing...")
                result = self.model.transcribe(audio_normalised, fp16=self.fp16, language=self.language)
                # Printing the transcribed text
                print(result['text'])
                # Decide if this text is directed to YOU/Your ID
                if self.id.lower() in result['text'].lower():  # If this is about me, send to consciousness
                    print("Passing to consciousness...")
                    message = {'from': '{}_ears'.format(self.id), 'message': result['text']}
                    self.consciousness_socket.send_json(message)


if __name__ == '__main__':
    b = Brain()
    b.process()
