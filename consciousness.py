#!/usr/bin/env python

import zmq
from pprint import pprint
from llama_cpp import Llama
from mouth import Mouth


class Consciousness:

    def __init__(self):
        self.context = zmq.Context()
        self.consciousness_relay = self.context.socket(zmq.PULL)
        self.consciousness_relay.bind("tcp://127.0.0.1:8001")
        self.max_tokens = 64
        self.echo = True
        self.llm = Llama(model_path="./models/ggml-model-q4_1.bin")
        self.mouth = Mouth()  # This should be refactored to be separate via zmq like brain and ears.

    def ponder_and_respond(self):
        # collector = {}  # Use to aggregate consciousness data if you wish.
        while True:
            work = self.consciousness_relay.recv_json()
            pprint(work)
            message = work.get('message', None)
            if message:
                output = self.llm(
                    "Q: {} A: ".format(message), max_tokens=self.max_tokens, stop=["Q:", "\n"], echo=self.echo)
                # pprint(output)
                choices = output.get("choices", None)
                if choices and len(choices) > 0:
                    try:
                        message = choices[0].get('text').split("A: ", 1)[1]
                        print("Asking mouth to speak...{}".format(message))
                        self.mouth.speak(message)
                    except AttributeError:
                        pprint({"~~~~ Error ~~~~": choices})


if __name__ == '__main__':
    c = Consciousness()
    c.ponder_and_respond()
