#!/usr/bin/env python

import json
import uuid
import zmq
from llama_cpp import Llama
from mouth import Mouth
from pyre import Pyre
from pyre import zhelper
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

    def ponder_and_respond(self, ctx, pipe):
        n = Pyre(self.id)
        n.set_header("id", self.id)
        n.set_header("type", "brain")
        n.join("CONSCIOUSNESS")
        n.start()

        poller = zmq.Poller()
        poller.register(pipe, zmq.POLLIN)
        # print(n.socket())
        poller.register(n.socket(), zmq.POLLIN)
        # print(n.socket())

        while True:
            items = dict(poller.poll())
            # print(n.socket(), items)
            if pipe in items and items[pipe] == zmq.POLLIN:  # Sent from self!
                message = pipe.recv().decode('utf-8')
                print("CONSCIOUSNESS MESSAGE: %s" % message)
                # message to quit
                if message == "$$STOP":  # This will throw an error if the data is not encoded
                    break
                n.shouts("CONSCIOUSNESS", message)
            else:  # Sent from brain!
                cmds = n.recv()
                msg_type = cmds.pop(0).decode('utf-8')
                msg_uuid = uuid.UUID(bytes=cmds.pop(0))
                msg_name = cmds.pop(0).decode('utf-8')
                # print("NODE_MSG TYPE: %s" % msg_type)
                # print("NODE_MSG PEER: %s" % msg_uuid)
                # print("NODE_MSG NAME: %s" % msg_name)
                if msg_type == "SHOUT":
                    msg_group = cmds.pop(0).decode('utf-8')
                    # print("NODE_MSG GROUP: %s" % msg_group)
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
                elif msg_type == "ENTER":  # This is where we register our organs.
                    headers = json.loads(cmds.pop(0).decode('utf-8'))

                # print("NODE_MSG CONT: %s" % cmds)
        n.stop()


if __name__ == '__main__':
    c = Consciousness()
