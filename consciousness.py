#!/usr/bin/env python

import json
import zmq
from llama_cpp import Llama
from mouth import Mouth
from pyre import Pyre
from pyre import zhelper
from environment import NETWORKS
from afferent_neuron import AfferentNeuron
# from pprint import pprint


class Consciousness:

    def __init__(self):
        self.id = "consciousness"
        self.context = zmq.Context()
        self.max_tokens = 64
        self.echo = True
        self.llm = Llama(model_path="./models/ggml-model-q4_1.bin")
        self.mouth = Mouth()  # This should be refactored to be separate via zmq like brain and ears.
        # Work to/from consciousness network
        self.consciousness_pipe = zhelper.zthread_fork(self.context, self.ponder_and_respond)

    def handle_introspection(self, n: Pyre, network: NETWORKS, message) -> str:
        if message.decode('utf-8') == "$$STOP":
            return "$$STOP"
        n.shouts(network.value, message.decode('utf-8'))
        return ""

    def handle_shout(self, msg_uuid, msg_name, msg_group, cmds):
        question = json.loads(cmds.pop(0))
        # pprint(question)
        output = self.llm(
            "Q: {} A: ".format(question['message']), max_tokens=self.max_tokens, stop=["Q:", "\n"], echo=self.echo)
        # pprint(output)
        choices = output.get("choices", None)
        if choices and len(choices) > 0:
            try:
                message = choices[0].get('text').split("A: ", 1)[1]
                print("Asking mouth to speak...{}".format(message))
                self.mouth.speak(message)
            except AttributeError as ae:
                print("~~~~ Error ~~~~\n%s" % ae)

    def ponder_and_respond(self, ctx, pipe):
        AfferentNeuron.process(self.id, "consciousness", pipe,
                               NETWORKS.CONSCIOUSNESS, self.handle_introspection, self.handle_shout)


if __name__ == '__main__':
    c = Consciousness()
